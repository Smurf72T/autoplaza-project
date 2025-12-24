# apps/analytics/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import TimeStampedModel, User


class PageView(TimeStampedModel):
    """Просмотры страниц для аналитики"""

    class Meta:
        db_table = 'page_views'
        verbose_name = _('Просмотр страницы')
        verbose_name_plural = _('Просмотры страниц')
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['page_url']),
            models.Index(fields=['viewed_at']),
            models.Index(fields=['user']),
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='page_views',
        verbose_name=_('Пользователь')
    )

    # Информация о странице
    page_url = models.URLField(_('URL страницы'), max_length=500)
    page_title = models.CharField(_('Заголовок страницы'), max_length=200, blank=True)
    referrer = models.URLField(_('Реферер'), max_length=500, blank=True)

    # Контекст
    car_ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='page_views',
        verbose_name=_('Объявление')
    )
    car_brand = models.ForeignKey(
        'catalog.CarBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Марка')
    )
    car_model = models.ForeignKey(
        'catalog.CarModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Модель')
    )

    # Техническая информация
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    session_id = models.CharField(_('ID сессии'), max_length=100, blank=True)
    device_type = models.CharField(_('Тип устройства'), max_length=50, blank=True)
    browser = models.CharField(_('Браузер'), max_length=100, blank=True)
    os = models.CharField(_('Операционная система'), max_length=100, blank=True)

    # Время
    viewed_at = models.DateTimeField(_('Время просмотра'), auto_now_add=True)
    time_on_page = models.IntegerField(_('Время на странице (сек)'), null=True, blank=True)

    def __str__(self):
        return f'Просмотр {self.page_url} в {self.viewed_at:%H:%M}'


class SearchAnalytics(TimeStampedModel):
    """Аналитика поисковых запросов"""

    class Meta:
        db_table = 'search_analytics'
        verbose_name = _('Аналитика поиска')
        verbose_name_plural = _('Аналитика поиска')
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['searched_at']),
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_analytics',
        verbose_name=_('Пользователь')
    )

    # Поисковый запрос
    query = models.CharField(_('Запрос'), max_length=200)
    filters = models.JSONField(_('Фильтры'), default=dict, blank=True)

    # Результаты
    results_count = models.IntegerField(_('Количество результатов'), null=True, blank=True)
    has_results = models.BooleanField(_('Есть результаты'), default=False)
    clicked_result = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_clicks',
        verbose_name=_('Кликнутое объявление')
    )

    # Техническая информация
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    session_id = models.CharField(_('ID сессии'), max_length=100, blank=True)

    # Время
    searched_at = models.DateTimeField(_('Время поиска'), auto_now_add=True)

    def __str__(self):
        return f'Поиск: "{self.query}"'


class UserActivity(TimeStampedModel):
    """Активность пользователей"""

    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Вход')
        LOGOUT = 'logout', _('Выход')
        REGISTER = 'register', _('Регистрация')
        VIEW_AD = 'view_ad', _('Просмотр объявления')
        CREATE_AD = 'create_ad', _('Создание объявления')
        EDIT_AD = 'edit_ad', _('Редактирование объявления')
        DELETE_AD = 'delete_ad', _('Удаление объявления')
        SEND_MESSAGE = 'send_message', _('Отправка сообщения')
        ADD_FAVORITE = 'add_favorite', _('Добавление в избранное')
        REMOVE_FAVORITE = 'remove_favorite', _('Удаление из избранного')
        SEARCH = 'search', _('Поиск')
        SUBSCRIBE = 'subscribe', _('Подписка')
        PAYMENT = 'payment', _('Оплата')

    class Meta:
        db_table = 'user_activities'
        verbose_name = _('Активность пользователя')
        verbose_name_plural = _('Активность пользователей')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['created_at']),
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_activities',
        verbose_name=_('Пользователь')
    )

    # Тип активности
    activity_type = models.CharField(
        _('Тип активности'),
        max_length=50,
        choices=ActivityType.choices
    )

    # Данные активности
    data = models.JSONField(_('Данные'), default=dict, blank=True)

    # Контекст
    car_ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name=_('Объявление')
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='targeted_activities',
        verbose_name=_('Целевой пользователь')
    )

    # IP и устройство
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)

    def __str__(self):
        return f'{self.user} - {self.get_activity_type_display()}'


class DailyStats(TimeStampedModel):
    """Ежедневная статистика"""

    class Meta:
        db_table = 'daily_stats'
        verbose_name = _('Ежедневная статистика')
        verbose_name_plural = _('Ежедневная статистика')
        ordering = ['-date']
        unique_together = ['date']

    date = models.DateField(_('Дата'), unique=True)

    # Пользователи
    new_users = models.IntegerField(_('Новые пользователи'), default=0)
    active_users = models.IntegerField(_('Активные пользователи'), default=0)

    # Объявления
    new_ads = models.IntegerField(_('Новые объявления'), default=0)
    active_ads = models.IntegerField(_('Активные объявления'), default=0)
    sold_ads = models.IntegerField(_('Проданные объявления'), default=0)

    # Просмотры
    total_views = models.IntegerField(_('Всего просмотров'), default=0)
    unique_views = models.IntegerField(_('Уникальные просмотры'), default=0)

    # Поиск
    searches = models.IntegerField(_('Поисковые запросы'), default=0)
    popular_searches = models.JSONField(_('Популярные запросы'), default=list, blank=True)

    # Сообщения
    messages_sent = models.IntegerField(_('Отправлено сообщений'), default=0)

    # Платежи
    payments_amount = models.DecimalField(
        _('Сумма платежей'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    payments_count = models.IntegerField(_('Количество платежей'), default=0)

    # Конверсии
    conversion_rate = models.DecimalField(
        _('Конверсия'),
        max_digits=5,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f'Статистика за {self.date}'

    class Meta:
        verbose_name = _('Ежедневная статистика')
        verbose_name_plural = _('Ежедневная статистика')


class ConversionEvent(TimeStampedModel):
    """События конверсии"""

    class EventType(models.TextChoices):
        VIEW_TO_CONTACT = 'view_to_contact', _('Просмотр → Контакт')
        CONTACT_TO_DEAL = 'contact_to_deal', _('Контакт → Сделка')
        SEARCH_TO_VIEW = 'search_to_view', _('Поиск → Просмотр')
        VIEW_TO_FAVORITE = 'view_to_favorite', _('Просмотр → Избранное')

    class Meta:
        db_table = 'conversion_events'
        verbose_name = _('Событие конверсии')
        verbose_name_plural = _('События конверсии')
        ordering = ['-created_at']

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversion_events',
        verbose_name=_('Пользователь')
    )

    car_ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.CASCADE,
        related_name='conversion_events',
        verbose_name=_('Объявление')
    )

    event_type = models.CharField(
        _('Тип события'),
        max_length=50,
        choices=EventType.choices
    )

    # Дополнительные данные
    data = models.JSONField(_('Данные'), default=dict, blank=True)
    session_id = models.CharField(_('ID сессии'), max_length=100, blank=True)

    def __str__(self):
        return f'{self.event_type} - {self.car_ad}'