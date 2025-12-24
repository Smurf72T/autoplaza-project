# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Основные страницы
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # Статистика
    path('stats/', views.StatsView.as_view(), name='stats'),

    # Юридические страницы
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms'),
    path('help/', views.HelpView.as_view(), name='help'),

    # SEO страницы
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap/', views.SiteMapView.as_view(), name='sitemap_html'),

    # Поиск
    path('search/', views.SearchView.as_view(), name='search'),

    # Топы
    path('top/brands/', views.TopBrandsView.as_view(), name='top_brands'),
    path('top/models/', views.TopModelsView.as_view(), name='top_models'),
    path('latest/', views.LatestAdsView.as_view(), name='latest_ads'),
    path('region/<str:region>/', views.AdsByRegionView.as_view(), name='ads_by_region'),

    # API для AJAX
    path('api/stats/', views.HomeStatsAPIView.as_view(), name='api_stats'),
    path('api/popular-brands/', views.PopularBrandsAPIView.as_view(), name='api_popular_brands'),
    path('api/recent-advertisements/', views.RecentAdsAPIView.as_view(), name='api_recent_ads'),
    path('api/region-stats/', views.RegionStatsAPIView.as_view(), name='api_region_stats'),
    path('api/search/autocomplete/', views.SearchAutocompleteAPIView.as_view(), name='api_search_autocomplete'),

    # Утилиты
    path('api/status/', views.check_site_status, name='api_status'),
    path('theme/toggle/', views.toggle_theme, name='toggle_theme'),
    path('theme/current/', views.get_current_theme, name='current_theme'),
]