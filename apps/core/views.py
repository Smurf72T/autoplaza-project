# apps/core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Min, Max, Avg, Sum, Prefetch
from django.urls import reverse_lazy
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.core.cache import cache
from django.utils import timezone
from django.views import View

# Импорты моделей из других приложений
from apps.catalog.models import CarBrand, CarModel, CarFeature
from apps.advertisements.models import CarAd, CarPhoto, CarAdFeature, FavoriteAd, SearchHistory, CarView
from apps.users.models import User
from apps.reviews.models import Review
from apps.analytics.models import PageView, SearchAnalytics


class HomePageView(TemplateView):
    """Главная страница сайта"""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Популярные марки (с логотипами)
        context['popular_brands'] = CarBrand.objects.filter(
            is_active=True
        ).annotate(
            models_count=Count('models'),
            ads_count=Count('models__advertisements', filter=Q(models__advertisements__status='active'))
        ).order_by('-ads_count')[:12]

        # Последние добавленные объявления
        context['recent_ads'] = CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related('model__brand', 'owner').prefetch_related('photos').order_by('-created_at')[:8]

        # Объявления с пометкой "топ" или "рекомендуемые"
        context['featured_ads'] = CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related('model__brand', 'owner').prefetch_related('photos').order_by('-views_count')[:6]

        # Статистика сайта
        context['total_ads'] = CarAd.objects.filter(status='active', is_active=True).count()
        context['total_brands'] = CarBrand.objects.filter(is_active=True).count()
        context['total_models'] = CarModel.objects.filter(is_active=True).count()
        context['total_users'] = User.objects.filter(is_active=True).count()

        # Поиск по популярным маркам
        context['search_suggestions'] = CarBrand.objects.filter(
            is_active=True
        ).annotate(
            ads_count=Count('models__advertisements', filter=Q(models__advertisements__status='active'))
        ).filter(ads_count__gt=0).order_by('-ads_count')[:10]

        # Регионы с наибольшим количеством объявлений
        context['top_regions'] = CarAd.objects.filter(
            status='active',
            is_active=True
        ).exclude(region='').values('region').annotate(
            count=Count('id')
        ).order_by('-count')[:6]

        return context

    def dispatch(self, request, *args, **kwargs):
        # Логируем просмотр главной страницы для аналитики
        if request.user.is_authenticated:
            PageView.objects.create(
                user=request.user,
                page_url=request.path,
                page_title='Главная страница',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        return super().dispatch(request, *args, **kwargs)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def about_view(request):
    """Страница 'О нас'"""
    context = {
        'title': 'О компании Autoplaza',
        'description': 'Autoplaza - крупнейшая площадка по продаже автомобилей в России',
        'stats': {
            'years_on_market': 5,
            'total_sales': 50000,
            'happy_customers': 100000,
            'partners': 2000,
        }
    }
    return render(request, 'core/about.html', context)

def contact_view(request):
    """Страница контактов"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Здесь должна быть логика отправки email
        messages.success(request, 'Сообщение успешно отправлено! Мы свяжемся с вами в ближайшее время.')
        return redirect('core:contact')

    context = {
        'title': 'Контакты',
        'contacts': {
            'phone': '+7 (800) 555-35-35',
            'email': 'info@autoplaza.ru',
            'address': 'Москва, ул. Автомобильная, д. 1',
            'work_hours': 'Пн-Пт: 9:00-18:00, Сб-Вс: 10:00-16:00',
        }
    }
    return render(request, 'core/contact.html', context)

class StatsView(TemplateView):
    """Страница статистики сайта"""
    template_name = 'core/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общая статистика
        context['total_stats'] = {
            'advertisements': CarAd.objects.filter(status='active', is_active=True).count(),
            'brands': CarBrand.objects.filter(is_active=True).count(),
            'models': CarModel.objects.filter(is_active=True).count(),
            'users': User.objects.filter(is_active=True).count(),
            'reviews': Review.objects.filter(is_approved=True).count(),
        }

        # Статистика за последние 30 дней
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

        context['recent_stats'] = {
            'new_ads': CarAd.objects.filter(created_at__gte=thirty_days_ago).count(),
            'new_users': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
            'sold_ads': CarAd.objects.filter(status='sold', updated_at__gte=thirty_days_ago).count(),
        }

        # Популярные марки
        context['popular_brands'] = CarBrand.objects.filter(
            is_active=True
        ).annotate(
            ads_count=Count('models__advertisements', filter=Q(models__advertisements__status='active'))
        ).order_by('-ads_count')[:10]

        # Популярные модели
        context['popular_models'] = CarModel.objects.filter(
            is_active=True
        ).annotate(
            ads_count=Count('advertisements', filter=Q(ads__status='active'))
        ).order_by('-ads_count')[:10]

        # Средние цены по маркам
        context['avg_prices'] = CarAd.objects.filter(
            status='active',
            is_active=True,
            price__isnull=False
        ).values('model__brand__name').annotate(
            avg_price=Avg('price'),
            count=Count('id')
        ).order_by('-avg_price')[:10]

        return context

def sitemap(request):
    """Генерирует sitemap.xml"""
    from django.template.loader import render_to_string

    # Основные страницы
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/about/', 'priority': '0.8', 'changefreq': 'monthly'},
        {'url': '/contact/', 'priority': '0.8', 'changefreq': 'monthly'},
        {'url': '/catalog/', 'priority': '0.9', 'changefreq': 'weekly'},
        {'url': '/advertisements/', 'priority': '0.9', 'changefreq': 'daily'},
    ]

    # Марки
    brands = CarBrand.objects.filter(is_active=True)[:1000]

    # Модели
    models = CarModel.objects.filter(is_active=True).select_related('brand')[:5000]

    # Объявления
    ads = CarAd.objects.filter(status='active', is_active=True)[:10000]

    xml_content = render_to_string('core/sitemap.xml', {
        'static_pages': static_pages,
        'brands': brands,
        'models': models,
        'advertisements': ads,
        'base_url': request.build_absolute_uri('/')[:-1],
    })

    return HttpResponse(xml_content, content_type='application/xml')

def robots_txt(request):
    """Генерирует robots.txt"""
    content = """User-agent: *
Disallow: /admin/
Disallow: /accounts/
Disallow: /api/
Disallow: /analytics/
Allow: /

Sitemap: https://autoplaza.ru/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

class PrivacyPolicyView(TemplateView):
    """Политика конфиденциальности"""
    template_name = 'core/privacy.html'

class TermsOfServiceView(TemplateView):
    """Условия использования"""
    template_name = 'core/terms.html'

class HelpView(TemplateView):
    """Помощь и FAQ"""
    template_name = 'core/help.html'

class SiteMapView(TemplateView):
    """Карта сайта (HTML версия)"""
    template_name = 'core/sitemap_html.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Все марки
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')

        # Основные категории моделей
        context['body_types'] = CarModel.objects.filter(
            is_active=True
        ).exclude(body_type='').values_list(
            'body_type', flat=True
        ).distinct().order_by('body_type')

        # Регионы
        context['regions'] = CarAd.objects.filter(
            status='active',
            is_active=True
        ).exclude(region='').values_list(
            'region', flat=True
        ).distinct().order_by('region')[:50]

        return context

class SearchView(TemplateView):
    """Общая страница поиска"""
    template_name = 'core/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()

        if query:
            # Логируем поиск
            if self.request.user.is_authenticated:
                SearchAnalytics.objects.create(
                    user=self.request.user,
                    query=query,
                    filters=self.request.GET.dict()
                )

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

            # Поиск по объявлениям
            ads = CarAd.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(model__name__icontains=query) |
                Q(model__brand__name__icontains=query) |
                Q(vin__icontains=query),
                status='active',
                is_active=True
            ).select_related('model__brand', 'owner').prefetch_related('photos')[:20]

            context.update({
                'brands': brands,
                'models': models,
                'advertisements': ads,
                'query': query,
                'results_count': brands.count() + models.count() + ads.count()
            })

        return context

class TopBrandsView(ListView):
    """Топ марок по количеству объявлений"""
    template_name = 'core/top_brands.html'
    context_object_name = 'brands'
    paginate_by = 20

    def get_queryset(self):
        return CarBrand.objects.filter(
            is_active=True
        ).annotate(
            ads_count=Count('models__advertisements', filter=Q(models__advertisements__status='active')),
            models_count=Count('models')
        ).filter(ads_count__gt=0).order_by('-ads_count')

class TopModelsView(ListView):
    """Топ моделей по количеству объявлений"""
    template_name = 'core/top_models.html'
    context_object_name = 'models'
    paginate_by = 20

    def get_queryset(self):
        return CarModel.objects.filter(
            is_active=True
        ).annotate(
            ads_count=Count('advertisements', filter=Q(ads__status='active'))
        ).filter(ads_count__gt=0).select_related('brand').order_by('-ads_count')

class LatestAdsView(ListView):
    """Последние объявления"""
    template_name = 'core/latest_ads.html'
    context_object_name = 'advertisements'
    paginate_by = 20

    def get_queryset(self):
        return CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related('model__brand', 'owner').prefetch_related('photos').order_by('-created_at')

class AdsByRegionView(ListView):
    """Объявления по регионам"""
    template_name = 'core/ads_by_region.html'
    context_object_name = 'advertisements'
    paginate_by = 20

    def get_queryset(self):
        region = self.kwargs.get('region')
        return CarAd.objects.filter(
            status='active',
            is_active=True,
            region__icontains=region
        ).select_related('model__brand', 'owner').prefetch_related('photos').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['region'] = self.kwargs.get('region')
        return context


# API Views для AJAX запросов

class HomeStatsAPIView(View):
    """API для получения статистики для главной страницы (AJAX)"""

    def get(self, request, *args, **kwargs):
        cache_key = 'home_stats'
        stats = cache.get(cache_key)

        if not stats:
            stats = {
                'total_ads': CarAd.objects.filter(status='active', is_active=True).count(),
                'total_brands': CarBrand.objects.filter(is_active=True).count(),
                'total_models': CarModel.objects.filter(is_active=True).count(),
                'total_users': User.objects.filter(is_active=True).count(),
                'popular_brands': list(
                    CarBrand.objects.filter(is_active=True)
                    .annotate(ads_count=Count('models__advertisements', filter=Q(models__advertisements__status='active')))
                    .filter(ads_count__gt=0)
                    .order_by('-ads_count')[:6]
                    .values('id', 'name', 'slug', 'logo')
                ),
                'recent_ads_count': CarAd.objects.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(days=7)
                ).count(),
            }
            cache.set(cache_key, stats, 300)  # 5 минут

        return JsonResponse(stats)

class PopularBrandsAPIView(View):
    """API для получения популярных марок (AJAX)"""

    def get(self, request, *args, **kwargs):
        limit = int(request.GET.get('limit', 10))

        brands = CarBrand.objects.filter(
            is_active=True
        ).annotate(
            ads_count=Count('models__advertisements', filter=Q(models__advertisements__status='active'))
        ).filter(ads_count__gt=0).order_by('-ads_count')[:limit]

        data = [
            {
                'id': brand.id,
                'name': brand.name,
                'slug': brand.slug,
                'country': brand.get_country_display(),
                'logo_url': brand.logo.url if brand.logo else None,
                'ads_count': brand.ads_count,
                'models_count': brand.models.count(),
            }
            for brand in brands
        ]

        return JsonResponse({'brands': data})

class RecentAdsAPIView(View):
    """API для получения последних объявлений (AJAX)"""

    def get(self, request, *args, **kwargs):
        limit = int(request.GET.get('limit', 6))

        ads = CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related('model__brand', 'owner').prefetch_related('photos').order_by('-created_at')[:limit]

        data = []
        for ad in ads:
            main_photo = ad.photos.filter(is_main=True).first()
            data.append({
                'id': ad.id,
                'title': ad.title,
                'slug': ad.slug,
                'price': float(ad.price),
                'currency': ad.price_currency,
                'year': ad.year,
                'mileage': ad.mileage,
                'brand': ad.model.brand.name,
                'model': ad.model.name,
                'city': ad.city,
                'created_at': ad.created_at.strftime('%d.%m.%Y'),
                'photo_url': main_photo.image.url if main_photo else None,
                'url': ad.get_absolute_url() if hasattr(ad, 'get_absolute_url') else f'/advertisements/{ad.slug}/',
            })

        return JsonResponse({'advertisements': data})

class RegionStatsAPIView(View):
    """API для получения статистики по регионам (AJAX)"""

    def get(self, request, *args, **kwargs):
        region_stats = CarAd.objects.filter(
            status='active',
            is_active=True
        ).exclude(region='').values('region').annotate(
            count=Count('id'),
            avg_price=Avg('price'),
            min_year=Min('year'),
            max_year=Max('year')
        ).order_by('-count')[:10]

        data = [
            {
                'region': stat['region'],
                'count': stat['count'],
                'avg_price': float(stat['avg_price'] or 0),
                'year_range': f"{stat['min_year'] or '?'}-{stat['max_year'] or '?'}",
            }
            for stat in region_stats
        ]

        return JsonResponse({'regions': data})

class SearchAutocompleteAPIView(View):
    """API для автодополнения поиска (AJAX)"""

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if len(query) < 2:
            return JsonResponse([], safe=False)

        results = []

        # Марки
        brands = CarBrand.objects.filter(
            name__icontains=query,
            is_active=True
        )[:5]

        for brand in brands:
            results.append({
                'type': 'brand',
                'id': brand.id,
                'name': brand.name,
                'slug': brand.slug,
                'display': f"{brand.name} (марка)",
                'url': f"/catalog/brands/{brand.slug}/",
                'logo': brand.logo.url if brand.logo else None,
            })

        # Модели
        models = CarModel.objects.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query),
            is_active=True
        ).select_related('brand')[:10]

        for model in models:
            results.append({
                'type': 'model',
                'id': model.id,
                'name': model.name,
                'brand': model.brand.name,
                'slug': model.slug,
                'display': f"{model.brand.name} {model.name} (модель)",
                'url': f"/catalog/models/{model.slug}/",
            })

        # Объявления (только заголовки)
        ads = CarAd.objects.filter(
            title__icontains=query,
            status='active',
            is_active=True
        )[:5]

        for ad in ads:
            results.append({
                'type': 'ad',
                'id': ad.id,
                'title': ad.title,
                'slug': ad.slug,
                'display': f"{ad.title[:50]}... (объявление)",
                'url': ad.get_absolute_url() if hasattr(ad, 'get_absolute_url') else f'/advertisements/{ad.slug}/',
            })

        return JsonResponse(results, safe=False)


@require_GET
def check_site_status(request):
    """Проверка статуса сайта (для мониторинга)"""
    from django.db import connection

    try:
        # Проверяем подключение к базе данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Проверяем наличие основных данных
        brands_count = CarBrand.objects.filter(is_active=True).count()
        models_count = CarModel.objects.filter(is_active=True).count()

        status = {
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'brands_count': brands_count,
            'models_count': models_count,
            'memory_usage': 'normal',
        }

        return JsonResponse(status)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)


# Декораторы для часто используемых функций

@login_required
def toggle_theme(request):
    """Переключение темы (темная/светлая)"""
    current_theme = request.session.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    request.session['theme'] = new_theme

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'theme': new_theme})

    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_GET
def get_current_theme(request):
    """Получить текущую тему"""
    theme = request.session.get('theme', 'light')
    return JsonResponse({'theme': theme})


# Error handlers

def handler404(request, exception):
    """Кастомная страница 404"""
    context = {
        'title': 'Страница не найдена',
        'error_code': 404,
        'error_message': 'Запрашиваемая страница не существует',
    }
    return render(request, '404.html', context, status=404)

def handler500(request):
    """Кастомная страница 500"""
    context = {
        'title': 'Ошибка сервера',
        'error_code': 500,
        'error_message': 'Внутренняя ошибка сервера',
    }
    return render(request, '500.html', context, status=500)

def handler403(request, exception):
    """Кастомная страница 403"""
    context = {
        'title': 'Доступ запрещен',
        'error_code': 403,
        'error_message': 'У вас нет прав для доступа к этой странице',
    }
    return render(request, '403.html', context, status=403)

def handler400(request, exception):
    """Кастомная страница 400"""
    context = {
        'title': 'Неверный запрос',
        'error_code': 400,
        'error_message': 'Некорректный запрос к серверу',
    }
    return render(request, '400.html', context, status=400)

from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token

@requires_csrf_token
def csrf_failure(request, reason=""):
    return render(request, '403_csrf.html', status=403)

# def handler404(request, exception):
#     return render(request, '404.html', status=404)

# def handler500(request):
#     return render(request, '500.html', status=500)

# def handler403(request, exception):
#     return render(request, '403.html', status=403)

# def handler400(request, exception):
#     return render(request, '400.html', status=400)