# apps/advertisements/urls.py
from django.urls import path
from . import views

app_name = 'advertisements'

urlpatterns = [
    # Список объявлений
    path('', views.AdvertisementsListView.as_view(), name='ad_list'),

    # Детали объявления
    path('<slug:slug>/', views.AdvertisementsDetailView.as_view(), name='ad_detail'),

    # Создание/редактирование объявления
    path('create/', views.CarAdCreateView.as_view(), name='ad_create'),  # Используем CarAdCreateView
    path('<slug:slug>/edit/', views.AdUpdateView.as_view(), name='ad_edit'),
    path('<slug:slug>/delete/', views.AdDeleteView.as_view(), name='ad_delete'),

    # Мои объявления
    path('my/', views.MyAdsView.as_view(), name='my_ads'),

    # Избранное
    path('favorites/', views.FavoritesView.as_view(), name='favorites'),

    # Действия с объявлениями
    path('<int:ad_id>/favorite/toggle/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:ad_id>/view/', views.increment_views, name='increment_views'),
    path('<slug:slug>/publish/', views.publish_ad, name='publish_ad'),
    path('<slug:slug>/unpublish/', views.unpublish_ad, name='unpublish_ad'),

    # Сообщения к объявлениям
    path('<int:ad_id>/message/send/', views.send_ad_message, name='send_ad_message'),

    # Экспорт
    path('export/csv/', views.export_ads_csv, name='export_csv'),

    # API endpoints
    path('api/search/', views.AdSearchAPIView.as_view(), name='api_search'),
    path('api/<int:ad_id>/similar/', views.SimilarAdsAPIView.as_view(), name='api_similar'),
]

# URL для фильтрации - ИСПРАВЛЕНО: используем FilteredAdListView
filter_patterns = [
    path('brand/<slug:brand_slug>/', views.FilteredAdListView.as_view(), name='filter_by_brand'),
    path('model/<slug:model_slug>/', views.FilteredAdListView.as_view(), name='filter_by_model'),
    path('city/<slug:city_slug>/', views.FilteredAdListView.as_view(), name='filter_by_city'),
    path('price/<int:min_price>/<int:max_price>/', views.FilteredAdListView.as_view(), name='filter_by_price'),
    path('year/<int:min_year>/<int:max_year>/', views.FilteredAdListView.as_view(), name='filter_by_year'),
]

urlpatterns += filter_patterns