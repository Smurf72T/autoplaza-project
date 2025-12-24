# apps/chat/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import TimeStampedModel, User


class ChatThread(TimeStampedModel):
    """Поток переписки между пользователями"""

    class Meta:
        db_table = 'chat_threads'
        verbose_name = _('Чат')
        verbose_name_plural = _('Чаты')
        ordering = ['-updated_at']
        unique_together = ['user1', 'user2']

    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_threads_as_user1',
        verbose_name=_('Пользователь 1')
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_threads_as_user2',
        verbose_name=_('Пользователь 2')
    )
    last_message = models.ForeignKey(
        'ChatMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('Последнее сообщение')
    )
    is_active = models.BooleanField(_('Активен'), default=True)

    def __str__(self):
        return f'Чат {self.user1} - {self.user2}'

    def get_other_user(self, user):
        """Получить собеседника"""
        return self.user2 if user == self.user1 else self.user1


class ChatMessage(TimeStampedModel):
    """Сообщение в чате"""

    class Meta:
        db_table = 'chat_messages'
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['thread', 'is_read']),
        ]

    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Чат')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('Отправитель')
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages_received',
        verbose_name=_('Получатель')
    )
    text = models.TextField(_('Текст сообщения'))

    # Связь с объявлением
    car_ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages',
        verbose_name=_('Объявление')
    )

    is_read = models.BooleanField(_('Прочитано'), default=False)
    read_at = models.DateTimeField(_('Время прочтения'), null=True, blank=True)

    # Для цитирования
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Ответ на')
    )

    def __str__(self):
        return f'Сообщение от {self.sender} ({self.created_at:%H:%M})'

    def mark_as_read(self):
        """Пометить как прочитанное"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class ChatNotification(TimeStampedModel):
    """Уведомления о новых сообщениях"""

    class Meta:
        db_table = 'chat_notifications'
        verbose_name = _('Уведомление чата')
        verbose_name_plural = _('Уведомления чата')
        ordering = ['-created_at']

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_notifications',
        verbose_name=_('Пользователь')
    )
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Сообщение')
    )
    is_read = models.BooleanField(_('Прочитано'), default=False)

    def __str__(self):
        return f'Уведомление для {self.user}'