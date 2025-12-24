# apps/catalog/urls.py
from django.urls import path
from . import views

app_name = 'cars'

urlpatterns = [
    # Основные страницы каталога - ИСПРАВЛЕНО: правильные имена
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('models/', views.ModelListView.as_view(), name='model_list'),
    path('models/<slug:slug>/', views.ModelDetailView.as_view(), name='model_detail'),

    # API - используем существующий метод
    path('api/models/', views.ModelListAPIView.as_view(), name='api_models'),
]

# admin_patterns = [
#     # дополнительные админские маршруты, если нужны
#     path('admin/something/', views.SomeAdminView.as_view(), name='admin_something'),
# ]
#
# urlpatterns += admin_patterns