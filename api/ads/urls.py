# api/advertisements/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.AdViewSet, basename='ad')

urlpatterns = [
    path('search/', views.AdSearchView.as_view(), name='search'),
    path('my/', views.MyAdsView.as_view(), name='my_ads'),
    path('<int:ad_id>/favorite/', views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('<int:ad_id>/similar/', views.SimilarAdsView.as_view(), name='similar_ads'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('stats/', views.AdStatsView.as_view(), name='stats'),
]

urlpatterns += router.urls