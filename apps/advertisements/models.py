# apps/advertisements/models.py
import os
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse  # ИСПРАВЛЕНО: правильный импорт
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.users.models import TimeStampedModel, User
from apps.catalog.models import CarBrand, CarModel, CarFeature


# Вспомогательные функции
def car_photo_path(instance, filename):
    """Путь для сохранения фотографий автомобилей"""
    ext = filename.split('.')[-1]
    filename = f'{instance.car_ad.id}_{instance.position:03d}.{ext}'
    return os.path.join('cars', 'photos', str(instance.car_ad.id), filename)


def current_year_plus_one():
    """Текущий год + 1 для валидатора"""
    return datetime.datetime.now().year + 1

class City(TimeStampedModel):
    """Города для объявлений"""

    class Meta:
        db_table = 'cities'
        verbose_name = _('Город')
        verbose_name_plural = _('Города')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'region']),
            models.Index(fields=['is_active']),
            models.Index(fields=['slug']),
        ]

    name = models.CharField(_('Название города'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120, unique=True)
    region = models.CharField(_('Регион/Область'), max_length=100)
    country = models.CharField(_('Страна'), max_length=100, default='Россия')

    # Географические данные
    latitude = models.DecimalField(
        _('Широта'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('Долгота'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Статистика
    population = models.IntegerField(_('Население'), null=True, blank=True)
    is_capital = models.BooleanField(_('Столица региона'), default=False)
    is_major_city = models.BooleanField(_('Крупный город'), default=False)

    # Системные поля
    is_active = models.BooleanField(_('Активен'), default=True)
    ads_count = models.IntegerField(_('Количество объявлений'), default=0)

    def __str__(self):
        return f'{self.name}, {self.region}'

    def save(self, *args, **kwargs):
        # Автоматическое создание slug
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(f"{self.name}-{self.region}")
            self.slug = base_slug

            # Проверка уникальности
            counter = 1
            original_slug = self.slug
            while City.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Автоматически определяем крупный город
        if self.population and self.population > 1000000:
            self.is_major_city = True

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """URL для фильтрации по городу"""
        from django.urls import reverse
        return reverse('advertisements:filter_by_city', kwargs={'city_slug': self.slug})

    def update_ads_count(self):
        """Обновить количество объявлений в городе"""
        from .models import CarAd
        count = CarAd.objects.filter(city=self, is_active=True, status='active').count()
        self.ads_count = count
        self.save(update_fields=['ads_count'])

    @property
    def full_name(self):
        """Полное название с регионом"""
        return f"{self.name}, {self.region}"

    @classmethod
    def get_popular_cities(cls, limit=20):
        """Получить популярные города (по количеству объявлений)"""
        return cls.objects.filter(
            is_active=True,
            ads_count__gt=0
        ).order_by('-ads_count')[:limit]

class CarAd(TimeStampedModel):
    """Объявления о продаже автомобилей - ОБЪЕДИНЕННАЯ МОДЕЛЬ"""

    # Константы выбора (из обоих моделей)
    class ConditionType(models.TextChoices):
        NEW = 'new', _('Новый')
        USED = 'used', _('С пробегом')
        SALVAGE = 'salvage', _('Аварийный')
        SPARE_PARTS = 'spare_parts', _('На запчасти')

    class OwnerType(models.TextChoices):
        PRIVATE = 'private', _('Частное лицо')
        DEALER = 'dealer', _('Дилер')

    class StatusType(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        ACTIVE = 'active', _('Активно')
        SOLD = 'sold', _('Продано')
        EXPIRED = 'expired', _('Истекло')
        BANNED = 'banned', _('Заблокировано')
        # Из старой модели:
        PUBLISHED = 'published', _('Опубликовано')
        PENDING = 'pending', _('На модерации')

    class FuelType(models.TextChoices):
        PETROL = 'petrol', _('Бензин')
        DIESEL = 'diesel', _('Дизель')
        ELECTRIC = 'electric', _('Электро')
        HYBRID = 'hybrid', _('Гибрид')
        GAS = 'gas', _('Газ')
        PETROL_GAS = 'petrol_gas', _('Бензин+Газ')

    class TransmissionType(models.TextChoices):
        MANUAL = 'manual', _('Механика')
        AUTOMATIC = 'automatic', _('Автомат')
        ROBOT = 'robot', _('Робот')
        VARIATOR = 'variator', _('Вариатор')

    class DriveType(models.TextChoices):
        FRONT = 'front', _('Передний')
        REAR = 'rear', _('Задний')
        FULL = 'full', _('Полный')
        ALL_WHEEL = 'all_wheel', _('Полный (AWD)')
        FOUR_WHEEL = 'four_wheel', _('4WD')

    class Meta:
        db_table = 'car_ads'
        verbose_name = _('Объявление')
        verbose_name_plural = _('Объявления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
            models.Index(fields=['slug']),
        ]

    # === Основная информация (из обеих моделей) ===
    title = models.CharField(_('Заголовок'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=220, unique=True, blank=True)
    description = models.TextField(_('Описание'))

    # === Цена (из обеих моделей) ===
    price = models.DecimalField(_('Цена'), max_digits=12, decimal_places=2)
    price_currency = models.CharField(
        _('Валюта'),
        max_length=3,
        default='RUB',
        choices=[
            ('RUB', '₽ Рубль'),
            ('USD', '$ Доллар'),
            ('EUR', '€ Евро'),
            ('KZT', '₸ Тенге'),
        ]
    )
    is_negotiable = models.BooleanField(_('Торг'), default=False)

    # === Связь с автомобилем (из обеих моделей) ===
    model = models.ForeignKey(
        CarModel,
        on_delete=models.CASCADE,
        related_name='advertisements',
        verbose_name=_('Модель')
    )
    # Дополнительная связь с маркой для удобства (из старой модели)
    brand = models.ForeignKey(
        CarBrand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ads_direct',
        verbose_name=_('Марка')
    )

    # === Детали автомобиля (объединяем) ===
    year = models.IntegerField(
        _('Год выпуска'),
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(current_year_plus_one)
        ]
    )
    vin = models.CharField(
        _('VIN'),
        max_length=17,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    mileage = models.IntegerField(
        _('Пробег'),
        validators=[MinValueValidator(0)],
        default=0
    )
    mileage_unit = models.CharField(
        _('Единица пробега'),
        max_length=10,
        default='км',
        choices=[
            ('км', 'Километры'),
            ('mi', 'Мили'),
        ]
    )

    # === Двигатель и трансмиссия (из обеих моделей) ===
    engine_volume = models.DecimalField(
        _('Объем двигателя'),
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True
    )
    engine_power = models.IntegerField(
        _('Мощность (л.с.)'),
        null=True,
        blank=True
    )
    fuel_type = models.CharField(
        _('Топливо'),
        max_length=20,
        choices=FuelType.choices,
        blank=True
    )
    transmission_type = models.CharField(
        _('Коробка передач'),
        max_length=20,
        choices=TransmissionType.choices,
        blank=True
    )
    drive_type = models.CharField(
        _('Привод'),
        max_length=20,
        choices=DriveType.choices,
        blank=True
    )

    # === Состояние (из обеих моделей) ===
    condition = models.CharField(
        _('Состояние'),
        max_length=20,
        choices=ConditionType.choices,
        default=ConditionType.USED
    )
    color_exterior = models.CharField(_('Цвет кузова'), max_length=50, blank=True)
    color_interior = models.CharField(_('Цвет салона'), max_length=50, blank=True)
    color = models.CharField(
        _('Цвет (общий)'),
        max_length=50,
        blank=True,
        help_text=_('Основной цвет автомобиля')
    )

    # === Владелец (из обеих моделей) ===
    owner_type = models.CharField(
        _('Тип владельца'),
        max_length=10,
        choices=OwnerType.choices,
        default=OwnerType.PRIVATE
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='advertisements',
        verbose_name=_('Владелец')
    )

    # === Локация (из обеих моделей) ===
    city = models.ForeignKey(
        'City',  # В КАВЫЧКАХ!
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advertisements',
        verbose_name=_('Город')
    )

    region = models.CharField(_('Регион'), max_length=100)

    # === Статус и статистика (объединяем) ===
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.DRAFT
    )
    views = models.IntegerField(_('Просмотры'), default=0)  # Из старой
    views_count = models.IntegerField(_('Просмотры (count)'), default=0)  # Из новой
    is_active = models.BooleanField(_('Активно'), default=True)
    is_new = models.BooleanField(_('Новое'), default=True)  # Из старой модели

    # === Системные поля (из новой модели) ===
    moderated_at = models.DateTimeField(_('Время модерации'), null=True, blank=True)
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_ads',
        verbose_name=_('Модератор')
    )

    # === Дополнительные опции (из обеих моделей) ===
    seats = models.PositiveSmallIntegerField(
        _('Количество мест'),
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(2, 9)]
    )
    doors = models.PositiveSmallIntegerField(
        _('Количество дверей'),
        null=True,
        blank=True,
        choices=[(2, '2'), (3, '3'), (4, '4'), (5, '5')]
    )
    steering_wheel = models.CharField(
        _('Расположение руля'),
        max_length=10,
        choices=[('left', 'Левый'), ('right', 'Правый')],
        default='left'
    )
    has_tuning = models.BooleanField(_('Есть тюнинг'), default=False)
    service_history = models.BooleanField(_('Есть сервисная история'), default=False)

    # Поля из старой модели для совместимости:
    features = models.ManyToManyField(
        CarFeature,
        through='CarAdFeature',
        related_name='advertisements',
        verbose_name=_('Характеристики'),
        blank=True
    )

    def __str__(self):
        return f'{self.title} - {self.price:,} {self.price_currency}'

    def save(self, *args, **kwargs):
        # Автоматическое заполнение slug (объединяем логику)
        if not self.slug:
            base_slug = slugify(f"{self.model.brand.name} {self.model.name} {self.year}")
            self.slug = base_slug

            # Проверка уникальности
            counter = 1
            original_slug = self.slug
            while CarAd.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Автоматическое заполнение brand из model.brand
        if not self.brand and self.model:
            self.brand = self.model.brand

        # Автоматическое обновление цветовых полей
        if self.color and not self.color_exterior:
            self.color_exterior = self.color

        # Объединяем счетчики просмотров
        if self.views and not self.views_count:
            self.views_count = self.views
        elif self.views_count and not self.views:
            self.views = self.views_count

        # Если объявление активно, обновляем moderated_at
        if self.status == 'active' and not self.moderated_at:
            from django.utils import timezone
            self.moderated_at = timezone.now()

        # Обновляем флаг is_new (первые 7 дней)
        from django.utils import timezone
        days_ago = (timezone.now() - self.created_at).days if self.created_at else 30
        self.is_new = days_ago < 7

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """URL для детальной страницы объявления"""
        return reverse('advertisements:ad_detail', kwargs={'slug': self.slug})

    def get_main_photo(self):
        """Получить главную фотографию (из старой модели)"""
        try:
            return self.photos.filter(is_main=True).first()
        except AttributeError:
            return None

    @property
    def age(self):
        """Возраст автомобиля в годах (из новой модели)"""
        from datetime import date
        if self.year:
            return date.today().year - self.year
        return None

    @property
    def is_available(self):
        """Доступно ли объявление (из новой модели)"""
        return self.status == 'active' and self.is_active

    @property
    def is_published(self):
        """Опубликовано ли объявление (из старой модели)"""
        return self.status in ['active', 'published']

    def increment_views(self):
        """Увеличить счетчик просмотров (объединяем)"""
        self.views += 1
        self.views_count += 1
        self.save(update_fields=['views', 'views_count'])

    def publish(self):
        """Опубликовать объявление"""
        self.status = 'active'
        self.is_active = True
        from django.utils import timezone
        self.moderated_at = timezone.now()
        self.save(update_fields=['status', 'is_active', 'moderated_at'])

    def unpublish(self):
        """Снять с публикации"""
        self.status = 'draft'
        self.save(update_fields=['status'])


# === МОДЕЛИ-КОМПАНЬОНЫ (оставляем без изменений, они уже хорошие) ===

class CarPhoto(TimeStampedModel):
    """Фотографии автомобилей в объявлениях"""

    class Meta:
        db_table = 'car_photos'
        verbose_name = _('Фотография автомобиля')
        verbose_name_plural = _('Фотографии автомобилей')
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(
                fields=['car_ad', 'is_main'],
                condition=models.Q(is_main=True),
                name='one_main_photo_per_car'
            )
        ]

    car_ad = models.ForeignKey(
        CarAd,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Объявление')
    )
    image = models.ImageField(_('Изображение'), upload_to=car_photo_path)
    thumbnail = models.ImageField(
        _('Миниатюра'),
        upload_to=car_photo_path,
        null=True,
        blank=True
    )
    is_main = models.BooleanField(_('Главное фото'), default=False)
    position = models.IntegerField(_('Позиция'), default=0)
    alt_text = models.CharField(_('Alt текст'), max_length=200, blank=True)

    def __str__(self):
        return f'Фото {self.position} для {self.car_ad}'

    def save(self, *args, **kwargs):
        # Если это первое фото для объявления, сделать его главным
        if not self.pk and not CarPhoto.objects.filter(car_ad=self.car_ad).exists():
            self.is_main = True

        # Если установлено главное фото, снять статус с других
        if self.is_main:
            CarPhoto.objects.filter(
                car_ad=self.car_ad,
                is_main=True
            ).exclude(
                pk=self.pk if self.pk else None
            ).update(is_main=False)

        super().save(*args, **kwargs)


class CarAdFeature(TimeStampedModel):
    """Связь характеристик с объявлениями"""

    class Meta:
        db_table = 'car_ad_features'
        verbose_name = _('Характеристика объявления')
        verbose_name_plural = _('Характеристики объявлений')
        unique_together = ['car_ad', 'feature']

    car_ad = models.ForeignKey(
        CarAd,
        on_delete=models.CASCADE,
        related_name='ad_features',
        verbose_name=_('Объявление')
    )
    feature = models.ForeignKey(
        CarFeature,
        on_delete=models.CASCADE,
        verbose_name=_('Характеристика')
    )
    value = models.CharField(_('Значение'), max_length=200, blank=True)

    def __str__(self):
        return f'{self.feature.name}: {self.value or "Да"}'


class FavoriteAd(TimeStampedModel):
    """Избранные объявления пользователей"""

    class Meta:
        db_table = 'favorite_ads'
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранные')
        unique_together = ['user', 'car_ad']

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='favorite_ads_list',  # ИЗМЕНИТЕ related_name
        verbose_name=_('Пользователь')
    )

    car_ad = models.ForeignKey(
        CarAd,
        on_delete=models.CASCADE,
        related_name='favorites_rel',  # Изменяем related_name чтобы избежать конфликта
        verbose_name=_('Объявление')
    )

    def __str__(self):
        return f'{self.user} → {self.car_ad}'


class SearchHistory(TimeStampedModel):
    """История поисковых запросов"""

    class Meta:
        db_table = 'search_history'
        verbose_name = _('История поиска')
        verbose_name_plural = _('История поиска')
        ordering = ['-created_at']

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_history',
        verbose_name=_('Пользователь')
    )
    search_query = models.TextField(_('Поисковый запрос'), blank=True)
    filters = models.JSONField(_('Фильтры'), default=dict, blank=True)
    results_count = models.IntegerField(
        _('Количество результатов'),
        null=True,
        blank=True
    )

    def __str__(self):
        return f'Поиск: {self.search_query[:50]}...'


class CarView(TimeStampedModel):
    """История просмотров объявлений"""

    class Meta:
        db_table = 'car_views'
        verbose_name = _('Просмотр')
        verbose_name_plural = _('Просмотры')
        ordering = ['-viewed_at']

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='car_views',
        verbose_name=_('Пользователь')
    )
    car_ad = models.ForeignKey(
        CarAd,
        on_delete=models.CASCADE,
        related_name='car_views',
        verbose_name=_('Объявление')
    )
    ip_address = models.GenericIPAddressField(
        _('IP адрес'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(_('User Agent'), blank=True)
    viewed_at = models.DateTimeField(_('Время просмотра'), auto_now_add=True)

    def __str__(self):
        return f'Просмотр {self.car_ad} в {self.viewed_at}'