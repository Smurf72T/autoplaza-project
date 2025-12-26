# apps/payments/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import TimeStampedModel, User


class SubscriptionPlan(TimeStampedModel):
    """Планы подписки"""

    class Meta:
        db_table = 'subscription_plans'
        verbose_name = _('План подписки')
        verbose_name_plural = _('Планы подписки')
        ordering = ['price']

    name = models.CharField(_('Название'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True, max_length=100)
    description = models.TextField(_('Описание'))

    # Цена
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Валюта'), max_length=3, default='RUB')
    billing_period = models.CharField(
        _('Период оплаты'),
        max_length=20,
        choices=[
            ('monthly', _('Ежемесячно')),
            ('quarterly', _('Квартально')),
            ('yearly', _('Ежегодно')),
        ],
        default='monthly'
    )

    # Лимиты
    max_ads = models.IntegerField(_('Макс. объявлений'), default=5)
    max_photos_per_ad = models.IntegerField(_('Макс. фото на объявление'), default=20)
    featured_days = models.IntegerField(_('Дней в топе'), default=0)
    boost_days = models.IntegerField(_('Дней буста'), default=0)
    analytics_access = models.BooleanField(_('Аналитика'), default=False)
    priority_support = models.BooleanField(_('Приоритетная поддержка'), default=False)

    # Статус
    is_active = models.BooleanField(_('Активен'), default=True)
    is_popular = models.BooleanField(_('Популярный'), default=False)

    def __str__(self):
        return f'{self.name} - {self.price} {self.currency}/{self.billing_period}'


class UserSubscription(TimeStampedModel):
    """Подписки пользователей"""

    class Meta:
        db_table = 'user_subscriptions'
        verbose_name = _('Подписка пользователя')
        verbose_name_plural = _('Подписки пользователей')
        ordering = ['-created_at']

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Пользователь')
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='user_subscriptions',
        verbose_name=_('План')
    )

    # Даты
    start_date = models.DateTimeField(_('Начало подписки'))
    end_date = models.DateTimeField(_('Окончание подписки'))
    auto_renew = models.BooleanField(_('Автопродление'), default=True)

    # Статус
    is_active = models.BooleanField(_('Активна'), default=True)
    is_trial = models.BooleanField(_('Пробная'), default=False)

    # Использование
    ads_used = models.IntegerField(_('Использовано объявлений'), default=0)
    featured_used = models.IntegerField(_('Использовано дней в топе'), default=0)
    boost_used = models.IntegerField(_('Использовано дней буста'), default=0)

    def __str__(self):
        return f'{self.user} - {self.plan}'

    @property
    def is_expired(self):
        """Проверить истекла ли подписка"""
        from django.utils import timezone
        return timezone.now() > self.end_date

    @property
    def days_left(self):
        """Сколько дней осталось"""
        from django.utils import timezone
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0


class Payment(TimeStampedModel):
    """Платежи"""

    class Status(models.TextChoices):
        PENDING = 'pending', _('Ожидает')
        COMPLETED = 'completed', _('Завершен')
        FAILED = 'failed', _('Неудачный')
        REFUNDED = 'refunded', _('Возвращен')
        CANCELLED = 'cancelled', _('Отменен')

    class PaymentMethod(models.TextChoices):
        CARD = 'card', _('Карта')
        BANK_TRANSFER = 'bank_transfer', _('Банковский перевод')
        PAYPAL = 'paypal', _('PayPal')
        YOOKASSA = 'yookassa', _('ЮKassa')
        SBERBANK = 'sberbank', _('Сбербанк')

    class Meta:
        db_table = 'payments'
        verbose_name = _('Платеж')
        verbose_name_plural = _('Платежи')
        ordering = ['-created_at']

    # Связи
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Пользователь')
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Подписка')
    )

    # Информация о платеже
    amount = models.DecimalField(_('Сумма'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Валюта'), max_length=3, default='RUB')
    description = models.TextField(_('Описание'), blank=True)

    # Статус и метод
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_method = models.CharField(
        _('Метод оплаты'),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD
    )

    # Технические поля
    transaction_id = models.CharField(
        _('ID транзакции'),
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    provider_response = models.JSONField(
        _('Ответ провайдера'),
        default=dict,
        blank=True
    )

    # Даты
    paid_at = models.DateTimeField(_('Оплачено'), null=True, blank=True)
    refunded_at = models.DateTimeField(_('Возвращено'), null=True, blank=True)

    def __str__(self):
        return f'{self.amount} {self.currency} - {self.user} ({self.status})'


class AdPromotion(TimeStampedModel):
    """Продвижение объявлений"""

    class PromotionType(models.TextChoices):
        FEATURED = 'featured', _('Топ')
        BOOST = 'boost', _('Буст')
        VIP = 'vip', _('VIP')
        URGENT = 'urgent', _('Срочно')

    class Meta:
        db_table = 'ad_promotions'
        verbose_name = _('Продвижение объявления')
        verbose_name_plural = _('Продвижения объявлений')
        ordering = ['-created_at']

    car_ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotions',
        verbose_name=_('Объявление')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ad_promotions',
        verbose_name=_('Пользователь')
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ad_promotions',
        verbose_name=_('Платеж')
    )

    # Тип продвижения
    promotion_type = models.CharField(
        _('Тип продвижения'),
        max_length=20,
        choices=PromotionType.choices
    )

    # Период
    start_date = models.DateTimeField(_('Начало'))
    end_date = models.DateTimeField(_('Окончание'))

    # Статус
    is_active = models.BooleanField(_('Активно'), default=True)

    def __str__(self):
        return f'{self.promotion_type} для {self.car_ad}'

    @property
    def days_left(self):
        """Сколько дней осталось"""
        from django.utils import timezone
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0