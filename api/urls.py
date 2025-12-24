# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'advertisements', views.AdViewSet, basename='ad')
router.register(r'brands', views.BrandViewSet, basename='brand')
router.register(r'models', views.ModelViewSet, basename='model')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')

urlpatterns = [
    # REST API
    path('v1/', include(router.urls)),

    # Публичные API endpoints
    path('v1/advertisements/search/', views.AdSearchView.as_view(), name='ad_search'),
    path('v1/models/by-brand/<int:brand_id>/', views.ModelsByBrandView.as_view(), name='models_by_brand'),
    path('v1/cities/', views.CityListView.as_view(), name='city_list'),
    path('v1/stats/', views.StatsView.as_view(), name='stats'),

    # Авторизация API
    path('v1/auth/', include('rest_framework.urls')),
    path('v1/auth/token/', views.CustomAuthToken.as_view(), name='api_token_auth'),

    # Действия пользователя
    path('v1/favorites/<int:ad_id>/toggle/', views.toggle_favorite, name='toggle_favorite'),
    path('v1/favorites/clear/', views.clear_favorites, name='clear_favorites'),

    # Проверка данных
    path('v1/check/username/', views.check_username, name='check_username'),
    path('v1/check/email/', views.check_email, name='check_email'),

    # Загрузка файлов
    path('v1/upload/photo/', views.upload_photo, name='upload_photo'),
]