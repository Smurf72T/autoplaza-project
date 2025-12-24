# apps/users/models_profile.py
from django.db import models
from .models import User

class Message(models.Model):
    """Модель сообщений между пользователями"""

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='profile_messages_sent',
        verbose_name='Отправитель'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='profile_messages_received',
        verbose_name='Получатель'
    )
    text = models.TextField('Текст сообщения', max_length=2000)
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)

    # Связь с объявлением (если сообщение относится к конкретному объявлению)
    ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name='Объявление'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', 'created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f'Сообщение от {self.sender} к {self.recipient}'

    def mark_as_read(self):
        """Пометить сообщение как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class UserActivity(models.Model):
    """Модель для отслеживания активности пользователей"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='profile_activities',
        verbose_name='Пользователь'
    )
    activity_type = models.CharField('Тип активности', max_length=50)
    ip_address = models.GenericIPAddressField('IP адрес', blank=True, null=True)
    user_agent = models.TextField('User Agent', blank=True, null=True)
    created_at = models.DateTimeField('Время активности', auto_now_add=True)

    class Meta:
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: {self.activity_type}'


class Notification(models.Model):
    """Модель уведомлений пользователей"""

    NOTIFICATION_TYPES = [
        ('message', 'Новое сообщение'),
        ('ad_published', 'Объявление опубликовано'),
        ('ad_rejected', 'Объявление отклонено'),
        ('ad_expired', 'Объявление истекло'),
        ('favorite', 'Добавление в избранное'),
        ('review', 'Новый отзыв'),
        ('system', 'Системное уведомление'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    notification_type = models.CharField(
        'Тип уведомления',
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField('Заголовок', max_length=200)
    message = models.TextField('Сообщение')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    # Ссылка на связанный объект
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: {self.title}'

class UserSettings(models.Model):
    """Расширенные настройки пользователя"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name='Пользователь'
    )

    # Настройки приватности
    show_email = models.BooleanField('Показывать email', default=False)
    show_phone = models.BooleanField('Показывать телефон', default=True)
    show_last_seen = models.BooleanField('Показывать время последнего посещения', default=True)

    # Настройки языка и региона
    language = models.CharField(
        'Язык',
        max_length=10,
        choices=[('ru', 'Русский'), ('en', 'English')],
        default='ru'
    )
    timezone = models.CharField(
        'Часовой пояс',
        max_length=50,
        default='Europe/Moscow'
    )

    # Настройки отображения
    theme = models.CharField(
        'Тема',
        max_length=20,
        choices=[('light', 'Светлая'), ('dark', 'Темная'), ('auto', 'Авто')],
        default='auto'
    )
    items_per_page = models.IntegerField(
        'Элементов на странице',
        default=20
    )

    class Meta:
        verbose_name = 'Настройки пользователя'
        verbose_name_plural = 'Настройки пользователей'

    def __str__(self):
        return f'Настройки {self.user}'