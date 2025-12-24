# apps/payments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import SubscriptionPlan, UserSubscription, Payment, AdPromotion
from apps.advertisements.models import CarAd


class SubscriptionPlansView(ListView):
    """Список планов подписки"""
    template_name = 'payments/plans.html'
    model = SubscriptionPlan
    context_object_name = 'plans'

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True).order_by('price')


class SubscribeView(LoginRequiredMixin, CreateView):
    """Оформление подписки"""
    template_name = 'payments/subscribe.html'
    model = Payment
    fields = ['payment_method']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        context['plan'] = get_object_or_404(SubscriptionPlan, id=plan_id)
        return context

    def form_valid(self, form):
        plan_id = self.kwargs.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        # Создаем подписку
        now = timezone.now()
        if plan.billing_period == 'monthly':
            end_date = now + timezone.timedelta(days=30)
        elif plan.billing_period == 'quarterly':
            end_date = now + timezone.timedelta(days=90)
        else:  # yearly
            end_date = now + timezone.timedelta(days=365)

        subscription = UserSubscription.objects.create(
            user=self.request.user,
            plan=plan,
            start_date=now,
            end_date=end_date,
            is_active=True
        )

        # Создаем платеж
        payment = form.save(commit=False)
        payment.user = self.request.user
        payment.subscription = subscription
        payment.amount = plan.price
        payment.currency = plan.currency
        payment.description = f'Подписка на {plan.name}'
        payment.status = 'pending'
        payment.save()

        # Здесь должна быть логика обработки платежа через платежную систему
        # В демо-версии просто помечаем как оплаченный
        payment.status = 'completed'
        payment.paid_at = now
        payment.save()

        messages.success(self.request, f'Подписка "{plan.name}" успешно оформлена!')
        return redirect('payments:subscription')


class UserSubscriptionView(LoginRequiredMixin, DetailView):
    """Информация о текущей подписке пользователя"""
    template_name = 'payments/subscription.html'
    context_object_name = 'subscription'

    def get_object(self):
        return get_object_or_404(
            UserSubscription,
            user=self.request.user,
            is_active=True
        )


class BoostAdView(LoginRequiredMixin, View):
    """Буст объявления"""

    def post(self, request, *args, **kwargs):
        ad_id = kwargs.get('ad_id')
        ad = get_object_or_404(CarAd, id=ad_id, owner=request.user)

        # Проверяем наличие активной подписки
        subscription = UserSubscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).first()

        if not subscription:
            messages.error(request, 'Для буста требуется активная подписка')
            return redirect('advertisements:ad_detail', slug=ad.slug)

        # Проверяем лимиты
        if subscription.boost_used >= subscription.plan.boost_days:
            messages.error(request, 'Лимит бустов исчерпан')
            return redirect('advertisements:ad_detail', slug=ad.slug)

        # Создаем продвижение
        now = timezone.now()
        end_date = now + timezone.timedelta(days=7)  # Буст на 7 дней

        AdPromotion.objects.create(
            car_ad=ad,
            user=request.user,
            promotion_type='boost',
            start_date=now,
            end_date=end_date,
            is_active=True
        )

        # Обновляем счетчик использованных бустов
        subscription.boost_used += 1
        subscription.save()

        messages.success(request, 'Объявление успешно забустировано!')
        return redirect('advertisements:ad_detail', slug=ad.slug)


class PaymentHistoryView(LoginRequiredMixin, ListView):
    """История платежей"""
    template_name = 'payments/history.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class WebhookView(View):
    """Webhook для обработки платежей"""

    def post(self, request, *args, **kwargs):
        # Здесь логика обработки webhook от платежной системы
        # В реальном проекте будет сложнее

        # Парсим данные
        event_data = request.POST

        # Находим платеж по transaction_id
        payment = get_object_or_404(
            Payment,
            transaction_id=event_data.get('transaction_id')
        )

        # Обновляем статус
        if event_data.get('status') == 'success':
            payment.status = 'completed'
            payment.paid_at = timezone.now()

            # Активируем подписку, если есть
            if payment.subscription:
                payment.subscription.is_active = True
                payment.subscription.save()
        else:
            payment.status = 'failed'

        payment.provider_response = event_data
        payment.save()

        return JsonResponse({'status': 'ok'})


class CancelSubscriptionView(LoginRequiredMixin, View):
    """Отмена подписки"""

    def post(self, request, *args, **kwargs):
        subscription = get_object_or_404(
            UserSubscription,
            user=request.user,
            is_active=True
        )

        subscription.is_active = False
        subscription.cancelled_at = timezone.now()
        subscription.save()

        messages.success(request, 'Подписка успешно отменена')
        return redirect('payments:plans')


class MakeFeaturedView(LoginRequiredMixin, View):
    """Сделать объявление Featured"""

    def post(self, request, *args, **kwargs):
        ad_id = kwargs.get('ad_id')
        ad = get_object_or_404(CarAd, id=ad_id, owner=request.user)

        # Проверяем наличие активной подписки
        subscription = UserSubscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).first()

        if not subscription:
            messages.error(request, 'Для размещения в Featured требуется активная подписка')
            return redirect('advertisements:ad_detail', slug=ad.slug)

        # Создаем продвижение
        now = timezone.now()
        end_date = now + timezone.timedelta(days=30)  # Featured на 30 дней

        AdPromotion.objects.create(
            car_ad=ad,
            user=request.user,
            promotion_type='featured',
            start_date=now,
            end_date=end_date,
            is_active=True
        )

        messages.success(request, 'Объявление теперь в разделе Featured!')
        return redirect('advertisements:ad_detail', slug=ad.slug)


class MakeTopAdView(LoginRequiredMixin, View):
    """Сделать объявление Топ-объявлением"""

    def post(self, request, *args, **kwargs):
        ad_id = kwargs.get('ad_id')
        ad = get_object_or_404(CarAd, id=ad_id, owner=request.user)

        # Проверяем наличие активной подписки
        subscription = UserSubscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gt=timezone.now()
        ).first()

        if not subscription:
            messages.error(request, 'Для размещения в Топ-объявлениях требуется активная подписка')
            return redirect('advertisements:ad_detail', slug=ad.slug)

        # Создаем продвижение
        now = timezone.now()
        end_date = now + timezone.timedelta(days=14)  # Топ на 14 дней

        AdPromotion.objects.create(
            car_ad=ad,
            user=request.user,
            promotion_type='top',
            start_date=now,
            end_date=end_date,
            is_active=True
        )

        messages.success(request, 'Объявление теперь в Топ-объявлениях!')
        return redirect('advertisements:ad_detail', slug=ad.slug)


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Страница оформления заказа"""
    template_name = 'payments/checkout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Здесь логика для получения информации о заказе
        return context


class PaymentSuccessView(TemplateView):
    """Страница успешной оплаты"""
    template_name = 'payments/success.html'


class PaymentCancelView(TemplateView):
    """Страница отмены оплаты"""
    template_name = 'payments/cancel.html'


# Функции для webhooks
def stripe_webhook(request):
    """Webhook для Stripe"""
    # Логика обработки Stripe webhook
    return JsonResponse({'status': 'received'})


def paypal_webhook(request):
    """Webhook для PayPal"""
    # Логика обработки PayPal webhook
    return JsonResponse({'status': 'received'})
