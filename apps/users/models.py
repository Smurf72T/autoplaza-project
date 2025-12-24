# apps/users/models.py
import datetime
import os
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

class UserManager(DjangoUserManager):
    """Кастомный менеджер пользователей"""

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """Единая кастомная модель пользователя для Autoplaza"""

    class Meta:
        db_table = 'users_user'
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-date_joined']

    # Исправляем конфликт related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('Группы'),
        blank=True,
        related_name='core_user_set',
        related_query_name='core_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('Права пользователя'),
        blank=True,
        related_name='core_user_permission_set',
        related_query_name='core_user_permission',
    )

    # Основные поля
    email = models.EmailField('Email', unique=True)
    phone = models.CharField(
        'Телефон',
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+7\d{10}$',
                message='Введите номер в формате +7XXXXXXXXXX'
            )
        ],
        blank=True,
        null=True
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True,
        default='avatars/default.jpg'
    )

    # Тип пользователя для Autoplaza
    class UserType(models.TextChoices):
        BUYER = 'buyer', _('Покупатель')
        SELLER = 'seller', _('Продавец')
        DEALER = 'dealer', _('Дилер')
        ADMIN = 'admin', _('Администратор')

    user_type = models.CharField(
        _('Тип пользователя'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.BUYER
    )

    # Дополнительные поля
    city = models.CharField('Город', max_length=100, blank=True, null=True)
    about = models.TextField('О себе', blank=True, null=True)
    birth_date = models.DateField('Дата рождения', blank=True, null=True)

    # Статусы и флаги
    is_email_verified = models.BooleanField('Email подтвержден', default=False)
    email_verification_token = models.CharField(
        'Токен подтверждения email',
        max_length=64,
        blank=True,
        null=True
    )
    email_verification_sent_at = models.DateTimeField(
        'Время отправки подтверждения',
        blank=True,
        null=True
    )

    # Настройки уведомлений
    receive_email_notifications = models.BooleanField(
        'Получать email-уведомления',
        default=True
    )
    receive_sms_notifications = models.BooleanField(
        'Получать SMS-уведомления',
        default=False
    )

    # Даты
    last_activity = models.DateTimeField('Последняя активность', auto_now=True)

    # Кастомный менеджер
    objects = UserManager()

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        """Полное имя пользователя"""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.username

    def get_avatar_url(self):
        """URL аватара пользователя"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return f'{settings.STATIC_URL}img/default-avatar.png'

    def generate_email_verification_token(self):
        """Генерация токена для подтверждения email"""
        self.email_verification_token = str(uuid.uuid4())
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def send_email_verification(self):
        """Отправка письма для подтверждения email"""
        if not self.email_verification_token:
            self.generate_email_verification_token()

        context = {
            'user': self,
            'verification_url': f"{settings.SITE_URL}/accounts/email/confirm/{self.id}/{self.email_verification_token}/",
            'site_name': settings.SITE_NAME
        }

        subject = 'Подтверждение email на Autoplaza'
        message = render_to_string('accounts/email_verification_email.txt', context)
        html_message = render_to_string('accounts/email_verification_email.html', context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message
        )

    def verify_email(self, token):
        """Подтверждение email"""
        if (self.email_verification_token == token and
                self.email_verification_sent_at and
                (timezone.now() - self.email_verification_sent_at).days < 7):
            self.is_email_verified = True
            self.email_verification_token = None
            self.email_verification_sent_at = None
            self.save()
            return True
        return False

    def update_last_activity(self):
        """Обновление времени последней активности"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


def dealer_logo_path(instance, filename):
    """Путь для сохранения логотипов дилеров"""
    ext = filename.split('.')[-1]
    filename = f'{instance.id}_logo.{ext}'
    return os.path.join('dealers', 'logos', filename)


class Dealer(models.Model):
    """Дилерские центры - оставляем оригинальную структуру"""

    class Meta:
        db_table = 'dealers'
        verbose_name = _('Дилерский центр')
        verbose_name_plural = _('Дилерские центры')
        ordering = ['company_name']

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='dealer', verbose_name=_('Пользователь'))
    company_name = models.CharField(_('Название компании'), max_length=200)
    legal_name = models.CharField(_('Юридическое название'), max_length=200, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    logo = models.ImageField(_('Логотип'), upload_to=dealer_logo_path,
                             null=True, blank=True)

    # Контакты
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)

    # Адрес
    address = models.TextField(_('Адрес'), blank=True)
    city = models.CharField(_('Город'), max_length=100)
    region = models.CharField(_('Регион'), max_length=100)
    postal_code = models.CharField(_('Почтовый индекс'), max_length=20, blank=True)
    latitude = models.DecimalField(_('Широта'), max_digits=10, decimal_places=8,
                                   null=True, blank=True)
    longitude = models.DecimalField(_('Долгота'), max_digits=11, decimal_places=8,
                                    null=True, blank=True)

    # Рейтинг
    rating = models.DecimalField(_('Рейтинг'), max_digits=3, decimal_places=2,
                                 default=0.0)
    reviews_count = models.IntegerField(_('Количество отзывов'), default=0)

    # Статус
    is_verified = models.BooleanField(_('Верифицирован'), default=False)
    is_active = models.BooleanField(_('Активен'), default=True)

    def __str__(self):
        return self.company_name

    @property
    def location_point(self):
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None


class DealerReview(models.Model):
    """Отзывы о дилерах"""

    class Meta:
        db_table = 'dealer_reviews'
        verbose_name = _('Отзыв о дилере')
        verbose_name_plural = _('Отзывы о дилерах')
        unique_together = ['dealer', 'user']
        ordering = ['-created_at']

    dealer = models.ForeignKey('Dealer', on_delete=models.CASCADE,
                               related_name='user_dealer_reviews', verbose_name=_('Дилер'))
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='dealer_reviews', verbose_name=_('Пользователь'))
    rating = models.IntegerField(_('Оценка'), validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ])
    comment = models.TextField(_('Комментарий'), blank=True)
    is_approved = models.BooleanField(_('Одобрено'), default=False)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)

    def __str__(self):
        return f'Отзыв {self.user} на {self.dealer}: {self.rating}/5'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_dealer_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_dealer_rating()

    def update_dealer_rating(self):
        reviews = DealerReview.objects.filter(dealer=self.dealer, is_approved=True)
        if reviews.exists():
            avg_rating = reviews.aggregate(avg=models.Avg('rating'))['avg']
            self.dealer.rating = round(avg_rating, 2)
            self.dealer.reviews_count = reviews.count()
        else:
            self.dealer.rating = 0.0
            self.dealer.reviews_count = 0
        self.dealer.save(update_fields=['rating', 'reviews_count'])


class TimeStampedModel(models.Model):
    """Абстрактная модель с временными метками"""
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)

    class Meta:
        abstract = True