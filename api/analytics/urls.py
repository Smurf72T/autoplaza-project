# api/analytics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('advertisements/', views.AdAnalyticsView.as_view(), name='advertisements'),
    path('users/', views.UserAnalyticsView.as_view(), name='users'),
    path('traffic/', views.TrafficAnalyticsView.as_view(), name='traffic'),
    path('reports/', views.GenerateReportView.as_view(), name='reports'),
]