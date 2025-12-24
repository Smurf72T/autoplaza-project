# api/catalog/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'brands', views.BrandViewSet)
router.register(r'models', views.ModelViewSet)

urlpatterns = [
    path('body-types/', views.BodyTypeListView.as_view(), name='body_types'),
    path('fuel-types/', views.FuelTypeListView.as_view(), name='fuel_types'),
    path('transmissions/', views.TransmissionListView.as_view(), name='transmissions'),
    path('specs/<int:model_id>/', views.ModelSpecsView.as_view(), name='model_specs'),
    path('compare/', views.CompareModelsView.as_view(), name='compare'),
]

urlpatterns += router.urls