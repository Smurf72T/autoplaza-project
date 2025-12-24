# apps/analytics/urls.py
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('advertisements/stats/', views.AdStatsView.as_view(), name='ad_stats'),
    path('users/stats/', views.UserStatsView.as_view(), name='user_stats'),
    path('traffic/', views.TrafficStatsView.as_view(), name='traffic'),
    path('conversions/', views.ConversionStatsView.as_view(), name='conversions'),

    # API endpoints
    path('api/daily-stats/', views.DailyStatsAPIView.as_view(), name='api_daily_stats'),
    path('api/popular-searches/', views.PopularSearchesAPIView.as_view(), name='api_popular_searches'),
    path('api/top-advertisements/', views.TopAdsAPIView.as_view(), name='api_top_ads'),
]