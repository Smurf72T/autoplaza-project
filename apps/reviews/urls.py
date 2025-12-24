# apps/reviews/urls.py
from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review_list'),
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('create/', views.ReviewCreateView.as_view(), name='review_create'),
    path('<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review_edit'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),
    path('user/<int:user_id>/', views.UserReviewsView.as_view(), name='user_reviews'),
    path('ad/<int:ad_id>/', views.AdReviewsView.as_view(), name='ad_reviews'),
    path('<int:pk>/like/', views.LikeReviewView.as_view(), name='like_review'),
    path('<int:pk>/dislike/', views.LikeReviewView.as_view(), name='dislike_review')
]