# apps/catalog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Count, Q, Avg, Min, Max
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.cache import cache
from apps.catalog.models import CarBrand, CarModel, CarFeature, CarFeatureCategory
from apps.advertisements.models import CarAd
from apps.reviews.models import Review
import json


class CatalogHomeView(TemplateView):
    """Главная страница каталога"""
    template_name = 'catalog/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Популярные марки (по количеству моделей)
        context['popular_brands'] = CarBrand.objects.filter(
            is_active=True
        ).annotate(
            models_count=Count('models')
        ).order_by('-models_count')[:12]

        # Последние добавленные модели
        context['recent_models'] = CarModel.objects.filter(
            is_active=True
        ).select_related('brand').order_by('-created_at')[:8]

        # Марки по странам
        context['brands_by_country'] = self.get_brands_by_country()

        # Статистика
        context['total_brands'] = CarBrand.objects.filter(is_active=True).count()
        context['total_models'] = CarModel.objects.filter(is_active=True).count()

        return context

    def get_brands_by_country(self):
        """Группировка марок по странам"""
        brands = CarBrand.objects.filter(is_active=True).order_by('country', 'name')
        countries = {}

        for brand in brands:
            country_code = brand.country
            country_name = brand.get_country_display()

            if country_name not in countries:
                countries[country_name] = {
                    'code': country_code,
                    'brands': []
                }

            countries[country_name]['brands'].append(brand)

        return countries


class BrandListView(ListView):
    """Список всех марок автомобилей"""
    model = CarBrand
    template_name = 'catalog/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 24  # По 24 марки на странице

    def get_queryset(self):
        queryset = CarBrand.objects.filter(is_active=True).annotate(
            models_count=Count('models')
        ).order_by('name')

        # Фильтрация по стране
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country=country)

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика по странам
        country_stats = CarBrand.objects.filter(
            is_active=True
        ).values('country').annotate(
            count=Count('id'),
            brands_list=Count('name', distinct=True)
        ).order_by('-count')

        # Добавляем отображаемые названия стран
        for stat in country_stats:
            try:
                brand = CarBrand.objects.filter(country=stat['country']).first()
                if brand:
                    stat['country_name'] = brand.get_country_display()
                else:
                    stat['country_name'] = stat['country']
            except:
                stat['country_name'] = stat['country']

        context['country_stats'] = country_stats
        context['current_country'] = self.request.GET.get('country')
        context['search_query'] = self.request.GET.get('search', '')

        return context


class BrandDetailView(DetailView):
    """Детальная страница марки автомобиля"""
    model = CarBrand
    template_name = 'catalog/brand_detail.html'
    context_object_name = 'brand'

    def get_queryset(self):
        return CarBrand.objects.filter(is_active=True).prefetch_related('models')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.object

        # Получаем все активные модели этой марки
        models = brand.models.filter(is_active=True).select_related('brand')

        # Группируем по типу кузова
        body_types = {}
        for model in models:
            body_type = model.body_type or 'Другой'
            if body_type not in body_types:
                body_types[body_type] = []
            body_types[body_type].append(model)

        # Статистика по годам выпуска
        years_range = models.aggregate(
            min_year=Min('year_start'),
            max_year=Max('year_end')
        )

        # Активные объявления этой марки
        active_ads = CarAd.objects.filter(
            model__brand=brand,
            status='active',
            is_active=True
        ).count()

        # Средняя цена объявлений
        price_stats = CarAd.objects.filter(
            model__brand=brand,
            status='active',
            is_active=True,
            price__isnull=False
        ).aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )

        context['body_types'] = body_types
        context['models'] = models
        context['models_count'] = models.count()
        context['years_range'] = years_range
        context['active_ads'] = active_ads
        context['price_stats'] = price_stats

        return context


class ModelListView(ListView):
    """Список всех моделей автомобилей"""
    model = CarModel
    template_name = 'catalog/model_list.html'
    context_object_name = 'models'
    paginate_by = 20

    def get_queryset(self):
        queryset = CarModel.objects.filter(
            is_active=True
        ).select_related('brand').order_by('brand__name', 'name')

        # Фильтры
        brand_id = self.request.GET.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)

        body_type = self.request.GET.get('body_type')
        if body_type:
            queryset = queryset.filter(body_type=body_type)

        # Фильтр по годам
        min_year = self.request.GET.get('min_year')
        if min_year:
            queryset = queryset.filter(year_start__gte=min_year)

        max_year = self.request.GET.get('max_year')
        if max_year:
            queryset = queryset.filter(
                Q(year_end__lte=max_year) | Q(year_end__isnull=True)
            )

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Все марки для фильтра
        context['all_brands'] = CarBrand.objects.filter(
            is_active=True
        ).order_by('name')

        # Типы кузова для фильтра
        context['body_types'] = CarModel.objects.filter(
            is_active=True
        ).exclude(body_type='').values_list(
            'body_type', flat=True
        ).distinct().order_by('body_type')

        # Текущие фильтры
        context['current_brand'] = self.request.GET.get('brand')
        context['current_body_type'] = self.request.GET.get('body_type')
        context['search_query'] = self.request.GET.get('search', '')

        return context


class ModelDetailView(DetailView):
    """Детальная страница модели автомобиля"""
    model = CarModel
    template_name = 'catalog/model_detail.html'
    context_object_name = 'model'

    def get_queryset(self):
        return CarModel.objects.filter(
            is_active=True
        ).select_related('brand')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model = self.object

        # Активные объявления этой модели
        active_ads = CarAd.objects.filter(
            model=model,
            status='active',
            is_active=True
        ).select_related('owner').prefetch_related('photos')[:6]

        # Статистика цен
        price_stats = CarAd.objects.filter(
            model=model,
            status='active',
            is_active=True,
            price__isnull=False
        ).aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            count=Count('id')
        )

        # Похожие модели (той же марки и типа кузова)
        similar_models = CarModel.objects.filter(
            brand=model.brand,
            body_type=model.body_type,
            is_active=True
        ).exclude(id=model.id).select_related('brand')[:6]

        # Отзывы о модели
        model_reviews = Review.objects.filter(
            car_ad__model=model,
            is_approved=True,
            review_type='car'
        ).select_related('author', 'car_ad')[:5]

        # Годы производства
        if model.year_start and model.year_end:
            years_produced = list(range(model.year_start, model.year_end + 1))
        elif model.year_start:
            years_produced = [model.year_start]
        else:
            years_produced = []

        context['active_ads'] = active_ads
        context['price_stats'] = price_stats
        context['similar_models'] = similar_models
        context['model_reviews'] = model_reviews
        context['years_produced'] = years_produced

        return context


class CompareView(TemplateView):
    """Сравнение моделей автомобилей"""
    template_name = 'catalog/compare.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем ID моделей из GET параметров
        model_ids = self.request.GET.get('models', '').split(',')
        model_ids = [int(id) for id in model_ids if id.isdigit()][:4]  # Макс 4 модели

        if model_ids:
            models = CarModel.objects.filter(
                id__in=model_ids,
                is_active=True
            ).select_related('brand')

            # Получаем характеристики для сравнения
            features = self.get_comparison_features(models)

            context['models'] = models
            context['features'] = features

        # Список всех моделей для выбора
        context['all_models'] = CarModel.objects.filter(
            is_active=True
        ).select_related('brand').order_by('brand__name', 'name')[:100]

        return context

    def get_comparison_features(self, models):
        """Получить характеристики для сравнения моделей"""
        features = {
            'Общие': [
                ('Марка', [model.brand.name for model in models]),
                ('Модель', [model.name for model in models]),
                ('Тип кузова', [model.body_type or 'Не указан' for model in models]),
                ('Годы выпуска', [
                    f"{model.year_start or '?'}-{model.year_end or 'н.в.'}"
                    for model in models
                ]),
            ],
            'Технические': [
                ('Двигатель', ['Не указано' for _ in models]),
                ('Мощность', ['Не указано' for _ in models]),
                ('Трансмиссия', ['Не указано' for _ in models]),
                ('Привод', ['Не указано' for _ in models]),
            ]
        }

        return features


class SearchView(TemplateView):
    """Страница поиска по каталогу"""
    template_name = 'catalog/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()

        if query:
            # Поиск по маркам
            brands = CarBrand.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query),
                is_active=True
            )[:10]

            # Поиск по моделям
            models = CarModel.objects.filter(
                Q(name__icontains=query) |
                Q(brand__name__icontains=query) |
                Q(description__icontains=query),
                is_active=True
            ).select_related('brand')[:20]

            # Поиск по характеристикам
            features = CarFeature.objects.filter(
                name__icontains=query
            )[:5]

            context.update({
                'brands': brands,
                'models': models,
                'features': features,
                'query': query,
                'results_count': brands.count() + models.count() + features.count()
            })

        return context


# ============================================================================
# АДМИНИСТРАТИВНЫЕ VIEW (только для админов и модераторов)
# ============================================================================

class BrandCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание новой марки автомобиля (только для админов)"""
    model = CarBrand
    template_name = 'catalog/brand_form.html'
    fields = ['name', 'country', 'description', 'logo']
    success_url = reverse_lazy('catalog:brand_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Марка "{form.instance.name}" успешно создана')
        return super().form_valid(form)


class BrandUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование марки автомобиля (только для админов)"""
    model = CarBrand
    template_name = 'catalog/brand_form.html'
    fields = ['name', 'country', 'description', 'logo', 'is_active']
    success_url = reverse_lazy('catalog:brand_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, f'Марка "{form.instance.name}" успешно обновлена')
        return super().form_valid(form)


class BrandDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление марки автомобиля (только для админов)"""
    model = CarBrand
    template_name = 'catalog/brand_confirm_delete.html'
    success_url = reverse_lazy('catalog:brand_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        brand = self.get_object()
        messages.success(request, f'Марка "{brand.name}" успешно удалена')
        return super().delete(request, *args, **kwargs)


class ModelCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание новой модели автомобиля (только для админов)"""
    model = CarModel
    template_name = 'catalog/model_form.html'
    fields = ['brand', 'name', 'body_type', 'year_start', 'year_end', 'description', 'image']
    success_url = reverse_lazy('catalog:model_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Модель "{form.instance.name}" успешно создана')
        return super().form_valid(form)


class ModelUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование модели автомобиля (только для админов)"""
    model = CarModel
    template_name = 'catalog/model_form.html'
    fields = ['brand', 'name', 'body_type', 'year_start', 'year_end', 'description', 'image', 'is_active']
    success_url = reverse_lazy('catalog:model_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Модель "{form.instance.name}" успешно обновлена')
        return super().form_valid(form)


class ModelDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление модели автомобиля (только для админов)"""
    model = CarModel
    template_name = 'catalog/model_confirm_delete.html'
    success_url = reverse_lazy('catalog:model_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        model = self.get_object()
        messages.success(request, f'Модель "{model.name}" успешно удалена')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# API VIEWS (для AJAX запросов)
# ============================================================================

class ModelListAPIView(View):
    """API для получения списка моделей по марке (AJAX)"""

    def get(self, request, *args, **kwargs):
        brand_id = request.GET.get('brand_id')

        if not brand_id:
            return JsonResponse([], safe=False)

        try:
            models = CarModel.objects.filter(
                brand_id=brand_id,
                is_active=True
            ).order_by('name')

            data = [
                {
                    'id': model.id,
                    'name': model.name,
                    'slug': model.slug,
                    'body_type': model.body_type or '',
                    'year_start': model.year_start,
                    'year_end': model.year_end,
                }
                for model in models
            ]

            return JsonResponse(data, safe=False)

        except Exception as e:
            return JsonResponse(
                {'error': str(e), 'message': 'Ошибка загрузки моделей'},
                status=400
            )


class BrandListAPIView(View):
    """API для получения списка марок (AJAX)"""

    def get(self, request, *args, **kwargs):
        brands = CarBrand.objects.filter(is_active=True).order_by('name')

        data = [
            {
                'id': brand.id,
                'name': brand.name,
                'slug': brand.slug,
                'country': brand.country,
                'country_name': brand.get_country_display(),
                'logo_url': brand.logo.url if brand.logo else None,
            }
            for brand in brands
        ]

        return JsonResponse(data, safe=False)


class BodyTypeListAPIView(View):
    """API для получения типов кузова (AJAX)"""

    def get(self, request, *args, **kwargs):
        body_types = CarModel.objects.filter(
            is_active=True
        ).exclude(
            Q(body_type='') | Q(body_type__isnull=True)
        ).values_list(
            'body_type', flat=True
        ).distinct().order_by('body_type')

        return JsonResponse(list(body_types), safe=False)


class SearchAutocompleteAPIView(View):
    """API для автодополнения поиска"""

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if len(query) < 2:
            return JsonResponse([], safe=False)

        # Поиск марок
        brands = CarBrand.objects.filter(
            name__icontains=query,
            is_active=True
        ).values('id', 'name', 'slug')[:5]

        # Поиск моделей
        models = CarModel.objects.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query),
            is_active=True
        ).select_related('brand').values(
            'id', 'name', 'slug', 'brand__name', 'brand__slug'
        )[:10]

        results = []

        # Добавляем марки
        for brand in brands:
            results.append({
                'type': 'brand',
                'id': brand['id'],
                'name': brand['name'],
                'slug': brand['slug'],
                'display': f"{brand['name']} (марка)",
                'url': f"/catalog/brands/{brand['slug']}/"
            })

        # Добавляем модели
        for model in models:
            results.append({
                'type': 'model',
                'id': model['id'],
                'name': model['name'],
                'brand': model['brand__name'],
                'slug': model['slug'],
                'display': f"{model['brand__name']} {model['name']} (модель)",
                'url': f"/catalog/models/{model['slug']}/"
            })

        return JsonResponse(results, safe=False)


class StatsAPIView(View):
    """API для получения статистики каталога"""

    def get(self, request, *args, **kwargs):
        cache_key = 'catalog_stats'
        stats = cache.get(cache_key)

        if not stats:
            stats = {
                'total_brands': CarBrand.objects.filter(is_active=True).count(),
                'total_models': CarModel.objects.filter(is_active=True).count(),
                'brands_by_country': self.get_brands_by_country_stats(),
                'popular_brands': self.get_popular_brands(),
                'recent_models': self.get_recent_models(),
            }
            cache.set(cache_key, stats, 300)  # Кэшируем на 5 минут

        return JsonResponse(stats)

    def get_brands_by_country_stats(self):
        brands = CarBrand.objects.filter(is_active=True)
        country_stats = {}

        for brand in brands:
            country = brand.get_country_display()
            if country not in country_stats:
                country_stats[country] = 0
            country_stats[country] += 1

        return country_stats

    def get_popular_brands(self):
        return list(CarBrand.objects.filter(
            is_active=True
        ).annotate(
            models_count=Count('models')
        ).order_by('-models_count')[:5].values('id', 'name', 'slug', 'logo'))

    def get_recent_models(self):
        return list(CarModel.objects.filter(
            is_active=True
        ).select_related('brand').order_by('-created_at')[:5].values(
            'id', 'name', 'slug', 'brand__name', 'brand__slug'
        ))