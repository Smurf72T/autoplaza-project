# apps/advertisements/urls.py
from django.urls import path
from . import views

app_name = 'advertisements'

urlpatterns = [
    path('test/<int:ad_id>/', views.test_ad_view, name='test_ad'), #test-path
    path('test-toggle/<int:ad_id>/', views.test_toggle_view, name='test_toggle'),

    # Список объявлений
    path('', views.AdvertisementsListView.as_view(), name='ad_list'),

    # API endpoints
    path('api/search/', views.AdSearchAPIView.as_view(), name='api_search'),
    path('api/<int:ad_id>/similar/', views.SimilarAdsAPIView.as_view(), name='api_similar'),

    # ДВА ПУТИ ДЛЯ API МОДЕЛЕЙ
    path('models-api/', views.api_models_by_brand, name='api_models_by_brand'),  # для совместимости
    path('api/models/', views.api_models_by_brand, name='api_models'),  # новый путь

    # Создание объявления
    path('create/', views.CarAdCreateView.as_view(), name='ad_create'),

    # Избранное
    path('favorites/', views.FavoriteAdListView.as_view(), name='favorites'),
    path('favorites/clear/', views.clear_favorites, name='clear_favorites'),

    # Мои объявления
    path('my/ads/', views.MyAdsView.as_view(), name='my_ads'),

    # Экспорт
    path('export/csv/', views.export_ads_csv, name='export_csv'),

    # ВАЖНО: Пути с ad_id должны быть ПЕРЕД путями со slug
    # Действия с объявлениями (используем id)
    path('<int:ad_id>/favorite/toggle/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:ad_id>/view/', views.increment_views, name='increment_views'),
    path('<int:ad_id>/send-message/', views.send_ad_message, name='send_ad_message'),

    # Пути со slug (должны быть ПОСЛЕ путей с id)
    path('<slug:slug>/publish/', views.publish_ad, name='publish_ad'),
    path('<slug:slug>/unpublish/', views.unpublish_ad, name='unpublish_ad'),
    path('<slug:slug>/edit/', views.AdUpdateView.as_view(), name='ad_edit'),
    path('<slug:slug>/delete/', views.AdDeleteView.as_view(), name='ad_delete'),

    # Детали объявления - ПОСЛЕДНИЙ из путей со slug
    path('<slug:slug>/', views.AdvertisementsDetailView.as_view(), name='ad_detail'),

    path('debug/ad/<int:ad_id>/', views.debug_ad, name='debug_ad'),
]

# URL для фильтрации
filter_patterns = [
    path('filter/brand/<slug:brand_slug>/', views.FilteredAdListView.as_view(), name='filter_by_brand'),
    path('filter/model/<slug:model_slug>/', views.FilteredAdListView.as_view(), name='filter_by_model'),
    path('filter/city/<slug:city_slug>/', views.FilteredAdListView.as_view(), name='filter_by_city'),
    path('filter/price/<int:min_price>/<int:max_price>/', views.FilteredAdListView.as_view(), name='filter_by_price'),
    path('filter/year/<int:min_year>/<int:max_year>/', views.FilteredAdListView.as_view(), name='filter_by_year'),
]

urlpatterns += filter_patterns