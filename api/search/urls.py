# api/search/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('advertisements/', views.AdSearchView.as_view(), name='advertisements'),
    path('cars/', views.CarSearchView.as_view(), name='cars'),
    path('users/', views.UserSearchView.as_view(), name='users'),
    path('suggestions/', views.SearchSuggestionsView.as_view(), name='suggestions'),
    path('filters/', views.SearchFiltersView.as_view(), name='filters'),
]