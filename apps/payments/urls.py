# apps/payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Подписки и платные услуги
    path('plans/', views.SubscriptionPlansView.as_view(), name='plans'),
    path('subscribe/<int:plan_id>/', views.SubscribeView.as_view(), name='subscribe'),
    path('subscription/', views.UserSubscriptionView.as_view(), name='subscription'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel_subscription'),

    # Платные размещения
    path('boost/<int:ad_id>/', views.BoostAdView.as_view(), name='boost_ad'),
    path('featured/<int:ad_id>/', views.MakeFeaturedView.as_view(), name='make_featured'),
    path('top/<int:ad_id>/', views.MakeTopAdView.as_view(), name='make_top_ad'),

    # Платежи
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),

    # Webhooks
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('webhook/paypal/', views.paypal_webhook, name='paypal_webhook'),
]