# apps/advertisements/views.py
import csv
import datetime
import logging

from apps.advertisements.forms import CarAdForm
from apps.catalog.models import CarBrand, CarModel, CarFeature
from apps.advertisements.models import CarAd, CarPhoto, CarAdFeature, FavoriteAd, SearchHistory, CarView
from apps.users.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count, Min, Max, Prefetch
from django.urls import reverse_lazy
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.core.cache import cache
from django.views import View
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__) # Получаем логгер для текущего модуля

class CarBrandListView(ListView):
    """Список всех марок автомобилей"""
    model = CarBrand
    template_name = 'catalog/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 12

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
        country_stats_raw = CarBrand.objects.filter(
            is_active=True
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')

        # Преобразуем код страны в читаемое название
        # Используем метод get_country_display() каждого бренда
        country_stats = []
        for stat in country_stats_raw:
            # Создаем временный объект бренда, чтобы получить отображаемое название страны
            try:
                # Получаем первый бренд с этой страной для получения отображаемого названия
                brand = CarBrand.objects.filter(country=stat['country']).first()
                if brand:
                    country_display = brand.get_country_display()
                else:
                    country_display = stat['country']
            except:
                country_display = stat['country']

            country_stats.append({
                'country': stat['country'],
                'get_country_display': country_display,
                'count': stat['count']
            })

        context['country_stats'] = country_stats

        return context


class CarBrandDetailView(DetailView):
    """Детальная страница марки автомобиля"""
    model = CarBrand
    template_name = 'catalog/brand_detail.html'
    context_object_name = 'brand'

    def get_queryset(self):
        return CarBrand.objects.filter(is_active=True).prefetch_related('models')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.object

        # Получаем модели этой марки
        models = brand.models.filter(is_active=True).order_by('name')

        # Группируем по типу кузова
        body_types = {}
        for model in models:
            body_type = model.body_type or 'другой'
            if body_type not in body_types:
                body_types[body_type] = []
            body_types[body_type].append(model)

        context['body_types'] = body_types
        context['models_count'] = models.count()

        return context


class CarModelListView(ListView):
    """Список всех моделей автомобилей"""
    model = CarModel
    template_name = 'catalog/model_list.html'
    context_object_name = 'models'
    paginate_by = 16

    def get_queryset(self):
        queryset = CarModel.objects.filter(
            is_active=True
        ).select_related('brand').order_by('brand__name', 'name')

        # Фильтрация по марке
        brand_id = self.request.GET.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)

        # Фильтрация по типу кузова
        body_type = self.request.GET.get('body_type')
        if body_type:
            queryset = queryset.filter(body_type=body_type)

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(brand__name__icontains=search)
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

        return context


class CarModelDetailView(DetailView):
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

        # Похожие модели (той же марки и типа кузова)
        similar_models = CarModel.objects.filter(
            brand=model.brand,
            is_active=True
        ).exclude(id=model.id).order_by('name')[:6]

        context['similar_models'] = similar_models

        return context


class SearchView(TemplateView):
    """Страница поиска"""
    template_name = 'advertisements/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')

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
                Q(brand__name__icontains=query),
                is_active=True
            ).select_related('brand')[:20]

            # Поиск по объявлениям
            ads = CarAd.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(model__name__icontains=query) |
                Q(model__brand__name__icontains=query),
                status='active',
                is_active=True
            ).select_related('model__brand').prefetch_related('photos')[:20]

            context['brands'] = brands
            context['models'] = models
            context['advertisements'] = ads
            context['query'] = query
            context['results_count'] = brands.count() + models.count() + ads.count()

        return context


def about_view(request):
    """Страница 'О нас'"""
    return render(request, 'core/about.html')


def contact_view(request):
    """Страница контактов"""
    return render(request, 'core/contact.html')


class AdvertisementsListView(ListView):
    """Список объявлений с расширенной фильтрацией"""
    model = CarAd
    template_name = 'advertisements/ad_list.html'
    context_object_name = 'advertisements'
    paginate_by = 20

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # Инициализируем переменные фильтров
        self.selected_brand = None
        self.selected_model = None
        self.current_sort = None
        self.current_order = None
        self.filter_params = {}

    def get_queryset(self):
        queryset = CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related(
            'model__brand',
            'owner'
        ).prefetch_related(
            'photos',
            Prefetch('ad_features__feature', queryset=CarAdFeature.objects.select_related('feature'))
        )

        # Получаем все GET-параметры
        params = self.request.GET
        self.filter_params = params.dict()

        # Сохраняем параметры для контекста
        self.selected_brand = params.get('brand')
        self.selected_model = params.get('model')
        self.current_sort = params.get('sort', '-created_at')
        self.current_order = params.get('order', 'desc')

        # 1. Фильтр по марке и модели
        brand_slug = params.get('brand')
        if brand_slug:
            # Ищем бренд по slug
            try:
                brand = CarBrand.objects.filter(slug=brand_slug).first()
                if brand:
                    queryset = queryset.filter(model__brand_id=brand.id)
                else:
                    # Если бренд не найден, возвращаем пустой queryset
                    queryset = queryset.none()
            except Exception:
                queryset = queryset.none()

        # 2. Фильтр по модели
        model_slug = params.get('model')
        if model_slug and brand_slug:  # Модель имеет смысл только если выбрана марка
            try:
                # Ищем модель по slug и марке
                brand = CarBrand.objects.filter(slug=brand_slug).first()
                if brand:
                    model = CarModel.objects.filter(slug=model_slug, brand=brand).first()
                    if model:
                        queryset = queryset.filter(model_id=model.id)
            except Exception:
                pass

        # 3. Фильтр по цене с валидацией
        min_price = params.get('min_price')
        max_price = params.get('max_price')

        if min_price:
            try:
                min_price_val = int(min_price)
                if min_price_val > 0:  # Только положительные значения
                    queryset = queryset.filter(price__gte=min_price_val)
            except ValueError:
                pass  # Игнорируем некорректные значения

        if max_price:
            try:
                max_price_val = int(max_price)
                if max_price_val > 0:  # Только положительные значения
                    queryset = queryset.filter(price__lte=max_price_val)
            except ValueError:
                pass  # Игнорируем некорректные значения

        # 4. Фильтр по году выпуска с валидацией
        min_year = params.get('min_year')
        max_year = params.get('max_year')

        if min_year:
            try:
                min_year_val = int(min_year)
                if 1900 <= min_year_val <= 2100:  # Реалистичные года
                    queryset = queryset.filter(year__gte=min_year_val)
            except ValueError:
                pass

        if max_year:
            try:
                max_year_val = int(max_year)
                if 1900 <= max_year_val <= 2100:  # Реалистичные года
                    queryset = queryset.filter(year__lte=max_year_val)
            except ValueError:
                pass

        # 5. Фильтр по пробегу с валидацией
        min_mileage = params.get('min_mileage')
        max_mileage = params.get('max_mileage')

        if min_mileage:
            try:
                min_mileage_val = int(min_mileage)
                if min_mileage_val >= 0:  # Пробег не может быть отрицательным
                    queryset = queryset.filter(mileage__gte=min_mileage_val)
            except ValueError:
                pass

        if max_mileage:
            try:
                max_mileage_val = int(max_mileage)
                if max_mileage_val >= 0:
                    queryset = queryset.filter(mileage__lte=max_mileage_val)
            except ValueError:
                pass

        # 6. Фильтр по типу кузова (из модели CarModel)
        body_type = params.get('body_type')
        if body_type:
            queryset = queryset.filter(model__body_type=body_type)

        # 7. Фильтры из модели CarAd (технические характеристики)
        filter_fields = [
            'fuel_type',  # Тип топлива
            'transmission_type',  # Коробка передач
            'drive_type',  # Привод
            'condition',  # Состояние
            'color_exterior',  # Цвет кузова
            'color_interior',  # Цвет салона
            'owner_type',  # Тип владельца (частник/дилер)
            'steering_wheel',  # Расположение руля
        ]

        for field in filter_fields:
            value = params.get(field)
            if value and value != 'all':  # 'all' можно использовать для "Все варианты"
                queryset = queryset.filter(**{field: value})

        # 8. Фильтр по объему двигателя с валидацией
        min_engine_volume = params.get('min_engine_volume')
        max_engine_volume = params.get('max_engine_volume')

        if min_engine_volume:
            try:
                min_volume = float(min_engine_volume)
                if min_volume > 0:
                    queryset = queryset.filter(engine_volume__gte=min_volume)
            except (ValueError, TypeError):
                pass

        if max_engine_volume:
            try:
                max_volume = float(max_engine_volume)
                if max_volume > 0:
                    queryset = queryset.filter(engine_volume__lte=max_volume)
            except (ValueError, TypeError):
                pass

        # 9. Фильтр по мощности двигателя с валидацией
        min_engine_power = params.get('min_engine_power')
        max_engine_power = params.get('max_engine_power')

        if min_engine_power:
            try:
                min_power = int(min_engine_power)
                if min_power > 0:
                    queryset = queryset.filter(engine_power__gte=min_power)
            except (ValueError, TypeError):
                pass

        if max_engine_power:
            try:
                max_power = int(max_engine_power)
                if max_power > 0:
                    queryset = queryset.filter(engine_power__lte=max_power)
            except (ValueError, TypeError):
                pass

        # 10. Фильтр по наличию сервисной истории и тюнингу
        if params.get('has_service_history') == 'true':
            queryset = queryset.filter(service_history=True)

        if params.get('has_tuning') == 'true':
            queryset = queryset.filter(has_tuning=True)

        # 11. Поиск по тексту (заголовок, описание, марка, модель)
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(model__name__icontains=search) |
                Q(model__brand__name__icontains=search) |
                Q(vin__icontains=search)
            )

        # 12. Фильтр по городу/региону
        city = params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        region = params.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)

        # 13. Фильтр по количеству дверей и мест
        doors = params.get('doors')
        if doors:
            try:
                doors_val = int(doors)
                if doors_val > 0:
                    queryset = queryset.filter(doors=doors_val)
            except ValueError:
                pass

        seats = params.get('seats')
        if seats:
            try:
                seats_val = int(seats)
                if seats_val > 0:
                    queryset = queryset.filter(seats=seats_val)
            except ValueError:
                pass

        # 14. Сортировка (после всех фильтров)
        sort_field = self.current_sort.replace('-', '') if self.current_sort.startswith('-') else self.current_sort
        if sort_field in ['price', 'year', 'created_at', 'mileage', 'views_count']:
            if self.current_order == 'asc':
                queryset = queryset.order_by(sort_field)
            else:
                queryset = queryset.order_by(f'-{sort_field}')
        else:
            # Сортировка по умолчанию - сначала новые
            queryset = queryset.order_by('-created_at')

        # Убираем дубликаты если есть
        queryset = queryset.distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем параметры запроса
        params = self.request.GET
        brand_id = params.get('brand')

        # Используем сохраненные атрибуты
        context['selected_brand'] = self.selected_brand
        context['selected_model'] = self.selected_model
        context['current_sort'] = self.current_sort.replace('-',
                                                            '') if self.current_sort and self.current_sort.startswith(
            '-') else self.current_sort
        context['current_order'] = self.current_order

        # Если текущая сортировка начинается с "-", значит order = 'desc'
        if self.current_sort and self.current_sort.startswith('-'):
            context['current_order'] = 'desc'
            context['current_sort'] = self.current_sort[1:]
        else:
            context['current_order'] = 'asc'

        # Используем кэш для часто запрашиваемых данных
        cache_key = f'filter_data_{brand_id}'
        filter_data = cache.get(cache_key)

        if not filter_data:
            filter_data = {}

            # Статистика для фильтров (минимальные/максимальные значения)
            # Используем базовый queryset без текущих фильтров
            base_qs = CarAd.objects.filter(
                status='active',
                is_active=True
            )

            # Если выбрана марка, фильтруем по ней
            if brand_id:
                if brand_id.isdigit():
                    # Это ID
                    base_qs = base_qs.filter(model__brand_id=int(brand_id))
                else:
                    # Это slug, находим ID по slug
                    try:
                        brand = CarBrand.objects.filter(slug=brand_id).first()
                        if brand:
                            base_qs = base_qs.filter(model__brand_id=brand.id)
                    except (ValueError, CarBrand.DoesNotExist):
                        pass  # Игнорируем некорректные значения

            # Вычисляем диапазоны
            filter_data['price_range'] = base_qs.aggregate(
                min_price=Min('price'),
                max_price=Max('price')
            )

            filter_data['year_range'] = base_qs.aggregate(
                min_year=Min('year'),
                max_year=Max('year')
            )

            filter_data['mileage_range'] = base_qs.aggregate(
                min_mileage=Min('mileage'),
                max_mileage=Max('mileage')
            )

            filter_data['engine_volume_range'] = base_qs.filter(
                engine_volume__isnull=False
            ).aggregate(
                min_volume=Min('engine_volume'),
                max_volume=Max('engine_volume')
            )

            filter_data['engine_power_range'] = base_qs.filter(
                engine_power__isnull=False
            ).aggregate(
                min_power=Min('engine_power'),
                max_power=Max('engine_power')
            )

            # Кэшируем на 5 минут
            cache.set(cache_key, filter_data, 300)

        # Добавляем данные из кэша в контекст
        context.update(filter_data)

        # Добавляем переменные для шаблона
        context['selected_brand'] = self.selected_brand
        context['selected_model'] = self.selected_model
        context['current_sort'] = self.current_sort
        context['current_order'] = self.current_order

        # Получаем все бренды для фильтра
        # Кэшируем список брендов
        brands_cache_key = 'all_brands_filter'
        all_brands = cache.get(brands_cache_key)

        if not all_brands:
            all_brands = CarBrand.objects.filter(
                is_active=True
            ).order_by('name')
            cache.set(brands_cache_key, all_brands, 3600)  # 1 час

        context['brands'] = all_brands

        # Если выбрана марка, получаем ее модели
        if self.selected_brand:
            models_cache_key = f'models_for_brand_{self.selected_brand}'
            models = cache.get(models_cache_key)

            if not models:
                # Проверяем, число ли это или slug
                if self.selected_brand.isdigit():
                    # Это ID
                    models = CarModel.objects.filter(
                        brand_id=int(self.selected_brand),
                        is_active=True
                    ).order_by('name')
                else:
                    # Это slug, ищем бренд
                    brand = CarBrand.objects.filter(slug=self.selected_brand).first()
                    if brand:
                        models = CarModel.objects.filter(
                            brand_id=brand.id,
                            is_active=True
                        ).order_by('name')
                    else:
                        models = CarModel.objects.none()

                cache.set(models_cache_key, models, 300)  # 5 минут

            context['models'] = models

        # Списки для выпадающих фильтров
        # Все марки, у которых есть активные объявления
        active_brands_cache_key = 'active_brands'
        active_brands = cache.get(active_brands_cache_key)

        if not active_brands:
            active_brands = CarBrand.objects.filter(
                models__advertisements__status='active',
                is_active=True
            ).distinct().order_by('name')
            cache.set(active_brands_cache_key, active_brands, 300)  # 5 минут

        context['active_brands'] = active_brands

        # Модели для фильтра (если выбрана марка)
        if brand_id:
            active_models_cache_key = f'active_models_{brand_id}'
            active_models = cache.get(active_models_cache_key)

            if not active_models:
                # Проверяем, является ли brand_id числом или slug
                if brand_id.isdigit():
                    # Это ID
                    brand_filter = {'brand_id': int(brand_id)}
                else:
                    # Это slug, ищем бренд
                    brand = CarBrand.objects.filter(slug=brand_id).first()
                    if brand:
                        brand_filter = {'brand_id': brand.id}
                    else:
                        brand_filter = {}  # Если бренд не найден

                if brand_filter:
                    active_models = CarModel.objects.filter(
                        **brand_filter,
                        advertisements__status='active',
                        advertisements__is_active=True,
                        is_active=True
                    ).distinct().order_by('name')
                else:
                    active_models = CarModel.objects.none()

                cache.set(active_models_cache_key, active_models, 300)

            context['active_models'] = active_models

        # Типы кузова для фильтра (только с активными объявлениями)
        body_types_cache_key = 'active_body_types'
        body_types = cache.get(body_types_cache_key)

        if not body_types:
            body_types = CarModel.objects.filter(
                advertisements__status='active',
                advertisements__is_active=True,
                is_active=True
            ).exclude(body_type='').values_list(
                'body_type', flat=True
            ).distinct().order_by('body_type')
            cache.set(body_types_cache_key, body_types, 300)

        context['body_types'] = body_types

        # Все доступные значения для фильтров из модели CarAd
        context['fuel_types'] = CarAd.FuelType.choices
        context['transmission_types'] = CarAd.TransmissionType.choices
        context['drive_types'] = CarAd.DriveType.choices
        context['condition_types'] = CarAd.ConditionType.choices
        context['owner_types'] = CarAd.OwnerType.choices

        # Уникальные цвета для фильтра (только активные объявления)
        colors_cache_key = 'active_colors'
        colors_data = cache.get(colors_cache_key)

        if not colors_data:
            colors_data = {
                'exterior_colors': CarAd.objects.filter(
                    status='active', is_active=True
                ).exclude(color_exterior='').values_list(
                    'color_exterior', flat=True
                ).distinct().order_by('color_exterior'),
                'interior_colors': CarAd.objects.filter(
                    status='active', is_active=True
                ).exclude(color_interior='').values_list(
                    'color_interior', flat=True
                ).distinct().order_by('color_interior')
            }
            cache.set(colors_cache_key, colors_data, 300)

        context.update(colors_data)

        # Города и регионы для фильтра
        locations_cache_key = 'active_locations'
        locations = cache.get(locations_cache_key)

        if not locations:
            locations = {
                'cities': CarAd.objects.filter(
                    status='active', is_active=True
                ).exclude(city_id=None).values_list(
                    'city', flat=True
                ).distinct().order_by('city')[:50],  # Ограничиваем до 50
                'regions': CarAd.objects.filter(
                    status='active', is_active=True
                ).exclude(region='').values_list(
                    'region', flat=True
                ).distinct().order_by('region')
            }
            cache.set(locations_cache_key, locations, 300)

        context.update(locations)

        # Уникальные значения для дверей и мест
        door_counts_cache_key = 'door_counts'
        door_counts = cache.get(door_counts_cache_key)

        if not door_counts:
            door_counts = {
                'door_options': CarAd.objects.filter(
                    status='active', is_active=True,
                    doors__isnull=False
                ).values_list('doors', flat=True).distinct().order_by('doors'),
                'seat_options': CarAd.objects.filter(
                    status='active', is_active=True,
                    seats__isnull=False
                ).values_list('seats', flat=True).distinct().order_by('seats')
            }
            cache.set(door_counts_cache_key, door_counts, 300)

        context.update(door_counts)

        # Сохраняем текущие параметры фильтрации для шаблона
        context['current_filters'] = self.request.GET.dict()

        # Добавляем общее количество объявлений в системе
        total_ads_cache_key = 'total_active_ads'
        total_ads = cache.get(total_ads_cache_key)

        if not total_ads:
            total_ads = CarAd.objects.filter(
                status='active', is_active=True
            ).count()
            cache.set(total_ads_cache_key, total_ads, 60)  # 1 минута

        context['total_active_ads'] = total_ads

        return context

    def get(self, request, *args, **kwargs):
        # Проверяем наличие некорректных параметров
        invalid_params = []

        # Проверяем числовые параметры
        numeric_params = ['min_price', 'max_price', 'min_year', 'max_year',
                          'min_mileage', 'max_mileage', 'min_engine_volume',
                          'max_engine_volume', 'min_engine_power', 'max_engine_power']

        for param in numeric_params:
            value = request.GET.get(param)
            if value:
                try:
                    if param in ['min_engine_volume', 'max_engine_volume']:
                        float(value)
                    else:
                        int(value)
                except ValueError:
                    invalid_params.append(param)

        if invalid_params:
            messages.warning(
                request,
                f'Некорректные значения в параметрах: {", ".join(invalid_params)}. Исправьте фильтры.'
            )

        # Сохраняем историю поиска для авторизованных пользователей
        if request.user.is_authenticated and len(request.GET) > 0:
            SearchHistory.objects.create(
                user=request.user,
                search_query=request.GET.get('search', ''),
                filters=request.GET.dict(),
                results_count=0  # Будет обновлено позже
            )

        return super().get(request, *args, **kwargs)


class AdvertisementsDetailView(DetailView):
    """Детальная страница объявления"""
    model = CarAd
    template_name = 'advertisements/ad_detail.html'
    context_object_name = 'ad'

    def get_queryset(self):
        return CarAd.objects.filter(
            is_active=True
        ).select_related(
            'model__brand', 'owner', 'moderator'
        ).prefetch_related(
            'photos', 'ad_features__feature'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ad = self.object

        # Увеличиваем счетчик просмотров
        ad.increment_views()

        # Сохраняем просмотр в историю
        if self.request.user.is_authenticated:
            CarView.objects.create(
                user=self.request.user,
                car_ad=ad,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )

        # Похожие объявления
        similar_ads = CarAd.objects.filter(
            model__brand=ad.model.brand,
            status='active',
            is_active=True
        ).exclude(id=ad.id).select_related(
            'model__brand'
        ).prefetch_related('photos').order_by('?')[:6]

        context['similar_ads'] = similar_ads

        # Проверяем, есть ли в избранном
        if self.request.user.is_authenticated:
            context['is_favorite'] = FavoriteAd.objects.filter(
                user=self.request.user,
                car_ad=ad
            ).exists()

        return context

    def get_object(self, queryset=None):
        try:
            obj = super().get_object(queryset)
            # Проверка доступа
            if not obj.is_active or obj.status != 'active':
                if not (self.request.user.is_staff or
                        self.request.user == obj.owner):
                    raise Http404("Объявление не найдено или не активно")
            return obj
        except CarAd.DoesNotExist:
            raise Http404("Объявление не найдено")


class CarAdCreateView(LoginRequiredMixin, CreateView):
    """Создание нового объявления"""
    form_class = CarAdForm
    template_name = 'advertisements/ad_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем список брендов в контекст для JavaScript
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')
        return context

    def form_valid(self, form):
        logger.info("=== FORM DATA DEBUG ===")
        logger.info(f"POST data: {self.request.POST}")
        logger.info(f"Files: {self.request.FILES}")
        logger.info(f"Form data: {form.cleaned_data}")

        if 'brand' in self.request.POST:
            brand_id = self.request.POST.get('brand')
            model_id = self.request.POST.get('model')
            logger.info(f"Brand from form: {brand_id}")
            logger.info(f"Model from form: {model_id}")

        # logger.info("Начата обработка формы создания объявления")
        # logger.debug(f"Данные формы: {form.cleaned_data}")

        form.instance.owner = self.request.user
        form.instance.owner_type = 'private' if not hasattr(self.request.user, 'dealer') else 'dealer'

        # Определяем статус в зависимости от кнопки
        if 'save_draft' in self.request.POST:
            form.instance.status = 'draft'
            message = 'Черновик сохранен'
        else:
            form.instance.status = 'draft'  # Или 'pending' для модерации
            message = 'Объявление создано и отправлено на модерацию'

        # Сохраняем объявление
        response = super().form_valid(form)

        # Обработка фото
        photos = self.request.FILES.getlist('photos')
        for i, photo in enumerate(photos):
            CarPhoto.objects.create(
                car_ad=self.object,
                image=photo,
                is_main=(i == 0),
                position=i
            )

        messages.success(self.request, message)
        return response

    def get_success_url(self):
        return reverse_lazy('advertisements:ad_detail', kwargs={'slug': self.object.slug})

class AdUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование объявления для advertisements namespace"""
    model = CarAd
    form_class = CarAdForm  # Используем CarAdForm вместо ограниченного набора полей
    template_name = 'advertisements/ad_form.html'

    def get_queryset(self):
        # Пользователь может редактировать только свои объявления
        return CarAd.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')
        return context

    def form_valid(self, form):
        # Определяем статус в зависимости от кнопки
        if 'save_draft' in self.request.POST:
            form.instance.status = 'draft'
            message = 'Черновик сохранен'
        else:
            form.instance.status = 'draft'  # Или 'pending' для модерации
            message = 'Объявление обновлено'

        # Сохраняем объявление
        response = super().form_valid(form)

        # Обработка новых фото
        photos = self.request.FILES.getlist('photos')
        for i, photo in enumerate(photos):
            CarPhoto.objects.create(
                car_ad=self.object,
                image=photo,
                is_main=(i == 0 and not self.object.photos.exists()),
                position=i + self.object.photos.count()
            )

        messages.success(self.request, message)
        return response

    def get_success_url(self):
        return reverse_lazy('advertisements:ad_detail', kwargs={'slug': self.object.slug})


class AdDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление объявления для advertisements namespace"""
    model = CarAd
    template_name = 'advertisements/ad_confirm_delete.html'
    success_url = reverse_lazy('advertisements:ad_list')

    def get_queryset(self):
        # Пользователь может удалять только свои объявления
        return CarAd.objects.filter(owner=self.request.user)


class MyAdsView(LoginRequiredMixin, ListView):
    """Мои объявления для advertisements namespace"""
    model = CarAd
    template_name = 'advertisements/my_ads.html'
    context_object_name = 'advertisements'

    def get_queryset(self):
        return CarAd.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')


class FavoriteAdListView(LoginRequiredMixin, ListView):
    """Список избранных объявлений"""
    model = FavoriteAd
    template_name = 'advertisements/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 20

    def get_queryset(self):
        return FavoriteAd.objects.filter(
            user=self.request.user
        ).select_related(
            'car_ad__model__brand'
        ).prefetch_related(
            'car_ad__photos'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавьте total_price в контекст
        total_price = sum(
            favorite.car_ad.price for favorite in context['favorites']
            if favorite.car_ad.price
        )
        context['total_price'] = total_price
        return context


# class FavoritesView(LoginRequiredMixin, ListView):
#     """Избранные объявления для advertisements namespace"""
#     model = FavoriteAd
#     template_name = 'advertisements/favorites.html'
#     context_object_name = 'favorites'
#
#     def get_queryset(self):
#         return FavoriteAd.objects.filter(
#             user=self.request.user
#         ).select_related('car_ad').order_by('-created_at')


@require_POST
@login_required
def toggle_favorite(request, ad_id):
    """Добавить/удалить из избранного"""
    ad = get_object_or_404(CarAd, id=ad_id, is_active=True, status='active')
    favorite, created = FavoriteAd.objects.get_or_create(
        user=request.user,
        car_ad=ad
    )

    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})

    return JsonResponse({'status': 'added'})


@login_required
def send_message(request):
    """Отправка сообщения продавцу"""
    if request.method == 'POST':
        ad_id = request.POST.get('ad_id')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        ad = get_object_or_404(CarAd, id=ad_id)

        # Здесь должна быть логика отправки сообщения
        # Например, сохранение в базу или отправка email

        messages.success(request, 'Сообщение отправлено продавцу')
        return redirect('advertisements:ad_detail', slug=ad.slug)

    return redirect('home')


@require_GET
def api_models_by_brand(request):
    """API для получения моделей автомобилей по бренду"""
    brand_id = request.GET.get('brand_id')
    brand_slug = request.GET.get('brand')

    print(f"=== API CALL ===")
    print(f"Brand ID from request: {brand_id}")
    print(f"Brand Slug from request: {brand_slug}")

    if not brand_id and not brand_slug:
        print("No brand_id or brand_slug provided")
        return JsonResponse([], safe=False)

    try:
        models_qs = CarModel.objects.filter(is_active=True)

        if brand_id:
            print(f"Looking for brand by ID: {brand_id}")
            # Пытаемся получить бренд по ID
            try:
                brand = CarBrand.objects.get(id=brand_id, is_active=True)
                print(f"Found brand: {brand.name} (ID: {brand.id})")
                models_qs = models_qs.filter(brand=brand)
            except (ValueError, CarBrand.DoesNotExist):
                print(f"Brand not found by ID: {brand_id}")
                return JsonResponse([], safe=False)
        elif brand_slug:
            print(f"Looking for brand by slug: {brand_slug}")
            # Получаем бренд по slug
            try:
                brand = CarBrand.objects.get(slug=brand_slug, is_active=True)
                models_qs = models_qs.filter(brand=brand)
            except CarBrand.DoesNotExist:
                return JsonResponse([], safe=False)

        # Получаем данные
        models = models_qs.order_by('name')
        print(f"Found {models.count()} models")

        data = []
        for model in models:
            model_data = {
                'id': model.id,
                'slug': model.slug,
                'name': model.name,
                'full_name': model.name
            }

            # Добавляем опциональные поля только если они есть
            if model.year_start:
                model_data['year_start'] = model.year_start
            if model.year_end:
                model_data['year_end'] = model.year_end
            if model.body_type:
                model_data['body_type'] = model.body_type

            data.append(model_data)

        print(f"Returning {len(data)} models")
        return JsonResponse(data, safe=False)

    except Exception as e:
        print(f"API Error: {str(e)}")
        logger.error(f"Ошибка в api_models_by_brand: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Internal server error', 'message': str(e)},
            status=500,
            safe=False
        )


@login_required
def increment_views(request, ad_id):
    """Увеличить счетчик просмотров для advertisements namespace"""
    ad = get_object_or_404(CarAd, id=ad_id)
    ad.increment_views()
    return JsonResponse({'views': ad.views_count})


@login_required
def publish_ad(request, slug):
    """Опубликовать объявление для advertisements namespace"""
    ad = get_object_or_404(CarAd, slug=slug, owner=request.user)
    ad.publish()
    messages.success(request, 'Объявление опубликовано')
    return redirect('advertisements:my_ads')


@login_required
def unpublish_ad(request, slug):
    """Снять с публикации для advertisements namespace"""
    ad = get_object_or_404(CarAd, slug=slug, owner=request.user)
    ad.unpublish()
    messages.success(request, 'Объявление снято с публикации')
    return redirect('advertisements:my_ads')


@login_required
def send_ad_message(request, ad_id):
    """Отправить сообщение по объявлению для advertisements namespace"""
    # Логика отправки сообщения
    ad = get_object_or_404(CarAd, id=ad_id)
    messages.success(request, 'Сообщение отправлено')
    return JsonResponse({'status': 'sent'})


def export_ads_csv(request):
    """Экспорт объявлений в CSV для advertisements namespace"""
    # Логика экспорта
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ads.csv"'
    # Здесь должна быть логика записи в CSV
    return response


class AdSearchAPIView(View):
    """API поиска объявлений для advertisements namespace"""

    def get(self, request):
        # Логика поиска
        search_query = request.GET.get('q', '')
        results = CarAd.objects.filter(
            status='active',
            is_active=True
        ).filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )[:10]

        data = [
            {
                'id': ad.id,
                'title': ad.title,
                'price': str(ad.price),
                'slug': ad.slug,
                'brand': ad.model.brand.name if ad.model and ad.model.brand else '',
                'model': ad.model.name if ad.model else '',
            }
            for ad in results
        ]

        return JsonResponse({'results': data})


class SimilarAdsAPIView(View):
    """API похожих объявлений для advertisements namespace"""

    def get(self, request, ad_id):
        try:
            ad = CarAd.objects.get(id=ad_id)
            similar_ads = CarAd.objects.filter(
                model__brand=ad.model.brand,
                status='active',
                is_active=True
            ).exclude(id=ad_id)[:6]

            data = [
                {
                    'id': similar_ad.id,
                    'title': similar_ad.title,
                    'price': str(similar_ad.price),
                    'slug': similar_ad.slug,
                    'image': similar_ad.get_main_photo().image.url if similar_ad.get_main_photo() else ''
                }
                for similar_ad in similar_ads
            ]

            return JsonResponse({'results': data})
        except CarAd.DoesNotExist:
            return JsonResponse({'error': 'Объявление не найдено'}, status=404)


@login_required
def send_ad_message(request, ad_id):
    """Отправить сообщение продавцу"""
    ad = get_object_or_404(CarAd, id=ad_id, is_active=True)

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()

        if not message_text:
            return JsonResponse({
                'status': 'error',
                'message': 'Сообщение не может быть пустым'
            })

        try:
            # Сохраняем сообщение (предполагаем, что есть модель Message)
            from apps.chat.models import Message

            message = Message.objects.create(
                sender=request.user,
                recipient=ad.owner,
                ad=ad,
                content=message_text
            )

            # Отправляем email уведомление
            if ad.owner.email:
                subject = f'Новое сообщение по вашему объявлению "{ad.title}"'
                context = {
                    'ad': ad,
                    'sender': request.user,
                    'message': message_text,
                    'site_url': settings.SITE_URL
                }

                html_message = render_to_string('emails/ad_message.html', context)
                text_message = render_to_string('emails/ad_message.txt', context)

                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ad.owner.email],
                    html_message=html_message,
                    fail_silently=True
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Сообщение успешно отправлено'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка отправки: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Неверный метод запроса'
    })


def export_ads_csv(request):
    """Экспорт объявлений в CSV"""
    if not request.user.is_authenticated:
        return HttpResponse('Требуется авторизация', status=401)

    # Создаем HTTP-ответ с CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response[
        'Content-Disposition'] = f'attachment; filename="autopaza_ads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    # Создаем CSV writer
    writer = csv.writer(response, delimiter=';')

    # Заголовки
    headers = [
        'ID',
        'Заголовок',
        'Марка',
        'Модель',
        'Год',
        'Цена (₽)',
        'Пробег',
        'Город',
        'Тип топлива',
        'Коробка передач',
        'Привод',
        'Состояние',
        'Дата создания',
        'Статус',
        'Просмотры',
        'Контакты',
        'VIN'
    ]
    writer.writerow(headers)

    # Получаем объявления
    ads = CarAd.objects.filter(owner=request.user).select_related('model__brand')

    for ad in ads:
        row = [
            ad.id,
            ad.title,
            ad.model.brand.name if ad.model and ad.model.brand else '',
            ad.model.name if ad.model else '',
            ad.year,
            ad.price,
            f"{ad.mileage} {ad.get_mileage_unit_display()}" if ad.mileage else '',
            ad.city,
            ad.get_fuel_type_display(),
            ad.get_transmission_type_display(),
            ad.get_drive_type_display(),
            ad.get_condition_display(),
            ad.created_at.strftime('%d.%m.%Y %H:%M'),
            ad.get_status_display(),
            ad.views_count,
            ad.contact_phone if hasattr(ad, 'contact_phone') else '',
            ad.vin or ''
        ]
        writer.writerow(row)

    return response

class FilteredAdListView(ListView):
    """Список объявлений для фильтрации по slug (для filter_patterns)"""
    model = CarAd
    template_name = 'advertisements/ad_list.html'
    context_object_name = 'advertisements'
    paginate_by = 20

    def get_queryset(self):
        queryset = CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related('model__brand', 'owner')

        # Обработка slug из URL
        if 'brand_slug' in self.kwargs:
            brand_slug = self.kwargs['brand_slug']
            queryset = queryset.filter(model__brand__slug=brand_slug)

        elif 'model_slug' in self.kwargs:
            model_slug = self.kwargs['model_slug']
            queryset = queryset.filter(model__slug=model_slug)

        elif 'city_slug' in self.kwargs:
            city_slug = self.kwargs['city_slug']
            queryset = queryset.filter(city__slug=city_slug)

        elif 'min_price' in self.kwargs and 'max_price' in self.kwargs:
            queryset = queryset.filter(
                price__gte=self.kwargs['min_price'],
                price__lte=self.kwargs['max_price']
            )

        elif 'min_year' in self.kwargs and 'max_year' in self.kwargs:
            queryset = queryset.filter(
                year__gte=self.kwargs['min_year'],
                year__lte=self.kwargs['max_year']
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем информацию о фильтре в контекст
        if 'brand_slug' in self.kwargs:
            try:
                brand = CarBrand.objects.get(slug=self.kwargs['brand_slug'])
                context['filter_title'] = f"Марка: {brand.name}"
            except CarBrand.DoesNotExist:
                context['filter_title'] = "Марка не найдена"

        elif 'model_slug' in self.kwargs:
            try:
                model = CarModel.objects.get(slug=self.kwargs['model_slug'])
                context['filter_title'] = f"Модель: {model.brand.name} {model.name}"
            except CarModel.DoesNotExist:
                context['filter_title'] = "Модель не найдена"

        return context


class FavoriteAdsView(LoginRequiredMixin, ListView):
    template_name = 'advertisements/favorites.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'ads': [], 'message': 'У вас пока нет избранных объявлений'})


@require_POST
@login_required
def clear_favorites(request):
    """Очистить все избранные объявления"""
    deleted_count, _ = FavoriteAd.objects.filter(user=request.user).delete()

    return JsonResponse({
        'success': True,
        'deleted_count': deleted_count
    })