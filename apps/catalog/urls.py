# apps/catalog/urls.py
from django.urls import path
from . import views

app_name = 'cars'

urlpatterns = [
    # Основные страницы каталога
    path('', views.CatalogHomeView.as_view(), name='home'),
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('models/', views.ModelListView.as_view(), name='model_list'),
    path('models/<slug:slug>/', views.ModelDetailView.as_view(), name='model_detail'),
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('search/', views.SearchView.as_view(), name='search'),

    # Административные маршруты
    path('brand/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brand/<int:pk>/edit/', views.BrandUpdateView.as_view(), name='brand_edit'),
    path('brand/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
    path('model/create/', views.ModelCreateView.as_view(), name='model_create'),
    path('model/<int:pk>/edit/', views.ModelUpdateView.as_view(), name='model_edit'),
    path('model/<int:pk>/delete/', views.ModelDeleteView.as_view(), name='model_delete'),

    # API endpoints
    path('api/models/', views.ModelListAPIView.as_view(), name='api_models'),
    path('api/brands/', views.BrandListAPIView.as_view(), name='api_brands'),
    path('api/body-types/', views.BodyTypeListAPIView.as_view(), name='api_body_types'),
    path('api/search/autocomplete/', views.SearchAutocompleteAPIView.as_view(), name='api_autocomplete'),
    path('api/stats/', views.StatsAPIView.as_view(), name='api_stats'),
]

# admin_patterns = [
#     # дополнительные админские маршруты, если нужны
#     path('admin/something/', views.SomeAdminView.as_view(), name='admin_something'),
# ]
#
# urlpatterns += admin_patterns