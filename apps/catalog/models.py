# apps/catalog/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
import os

from apps.users.models import TimeStampedModel


def car_brand_logo_path(instance, filename):
    """Путь для сохранения логотипов марок"""
    ext = filename.split('.')[-1]
    filename = f'{instance.slug}_logo.{ext}'
    return os.path.join('brands', 'logos', filename)


def car_model_image_path(instance, filename):
    """Путь для сохранения изображений моделей"""
    ext = filename.split('.')[-1]
    filename = f'{instance.slug}_{instance.brand.slug}.{ext}'
    return os.path.join('models', 'images', filename)


class CarBrand(TimeStampedModel):
    """Марки автомобилей"""

    class Meta:
        db_table = 'car_brands'
        verbose_name = _('Марка автомобиля')
        verbose_name_plural = _('Марки автомобилей')

    name = models.CharField(_('Название'), max_length=100, unique=True)
    slug = models.SlugField(_('Slug'), max_length=120, unique=True)
    country = models.CharField(_('Страна'), max_length=2, default='RU')
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активно'), default=True)
    logo = models.ImageField(
        _('Логотип'),
        upload_to=car_brand_logo_path,
        null=True,
        blank=True,
        help_text=_('Рекомендуемый размер: 300x300 пикселей')
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """URL для детальной страницы марки"""
        from django.urls import reverse
        return reverse('catalog:brand_detail', kwargs={'slug': self.slug})

    def get_country_display(self):
        """Получить отображаемое название страны"""
        country_names = {
            'RU': 'Россия',
            'DE': 'Германия',
            'JP': 'Япония',
            'US': 'США',
            'KR': 'Южная Корея',
            'FR': 'Франция',
            'IT': 'Италия',
            'GB': 'Великобритания',
            'CN': 'Китай',
            'CZ': 'Чехия',
            'SE': 'Швеция',
        }
        return country_names.get(self.country, self.country)


class CarModel(TimeStampedModel):
    """Модели автомобилей"""

    class Meta:
        db_table = 'car_models'
        verbose_name = _('Модель автомобиля')
        verbose_name_plural = _('Модели автомобилей')

    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE,
                              related_name='models', verbose_name=_('Марка'))
    name = models.CharField(_('Название модели'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=120, unique=True)
    body_type = models.CharField(_('Тип кузова'), max_length=50, blank=True)
    year_start = models.IntegerField(_('Год начала выпуска'), null=True, blank=True)
    year_end = models.IntegerField(_('Год окончания выпуска'), null=True, blank=True)
    is_active = models.BooleanField(_('Активно'), default=True)
    description = models.TextField(_('Описание'), blank=True)
    image = models.ImageField(
        _('Изображение'),
        upload_to=car_model_image_path,
        null=True,
        blank=True,
        help_text=_('Рекомендуемый размер: 800x600 пикселей')
    )

    def __str__(self):
        return f'{self.brand.name} {self.name}'

    def get_absolute_url(self):
        """URL для детальной страницы модели"""
        from django.urls import reverse
        return reverse('catalog:model_detail', kwargs={'slug': self.slug})

    @property
    def full_name(self):
        """Полное название модели с маркой"""
        return f"{self.brand.name} {self.name}"

    @property
    def is_currently_produced(self):
        """Производится ли модель в настоящее время"""
        from datetime import datetime
        current_year = datetime.now().year
        if self.year_end:
            return current_year <= self.year_end
        return True  # Если год окончания не указан, считаем что производится


class CarFeatureCategory(models.TextChoices):
    SAFETY = 'safety', _('Безопасность')
    COMFORT = 'comfort', _('Комфорт')
    MULTIMEDIA = 'multimedia', _('Мультимедиа')
    EXTERIOR = 'exterior', _('Экстерьер')
    INTERIOR = 'interior', _('Интерьер')
    OTHER = 'other', _('Другое')


class CarFeature(TimeStampedModel):
    """Характеристики автомобилей"""

    class Meta:
        db_table = 'car_features'
        verbose_name = _('Характеристика')
        verbose_name_plural = _('Характеристики')
        ordering = ['category', 'position']

    name = models.CharField(_('Название'), max_length=100)
    category = models.CharField(_('Категория'), max_length=50,
                                choices=CarFeatureCategory.choices)
    icon = models.CharField(_('Иконка'), max_length=50, blank=True)
    is_filterable = models.BooleanField(_('Для фильтра'), default=False)
    position = models.IntegerField(_('Позиция'), default=0)

    def __str__(self):
        return self.name