# apps/advertisements/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from pyexpat.errors import messages

from .models import CarAd, CarPhoto, CarAdFeature, FavoriteAd, SearchHistory, CarView


# ==============================
# КЛАССЫ ФИЛЬТРОВ
# ==============================

class StatusFilter(SimpleListFilter):
    """Фильтр по статусу объявления"""
    title = _('Статус')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Активные')),
            ('draft', _('Черновики')),
            ('pending', _('На модерации')),
            ('sold', _('Проданные')),
            ('expired', _('Истекшие')),
            ('banned', _('Заблокированные')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status='active', is_active=True)
        elif self.value() == 'draft':
            return queryset.filter(status='draft')
        elif self.value() == 'pending':
            return queryset.filter(status='pending')
        elif self.value() == 'sold':
            return queryset.filter(status='sold')
        elif self.value() == 'expired':
            return queryset.filter(status='expired')
        elif self.value() == 'banned':
            return queryset.filter(status='banned')
        return queryset


class OwnerTypeFilter(SimpleListFilter):
    """Фильтр по типу владельца"""
    title = _('Тип владельца')
    parameter_name = 'owner_type'

    def lookups(self, request, model_admin):
        return CarAd.OwnerType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(owner_type=self.value())
        return queryset


class NewAdsFilter(SimpleListFilter):
    """Фильтр по новым объявлениям (созданы за последние 7 дней)"""
    title = _('Новые')
    parameter_name = 'is_new'

    def lookups(self, request, model_admin):
        return (
            ('new', _('Новые (7 дней)')),
            ('old', _('Старые (>7 дней)')),
        )

    def queryset(self, request, queryset):
        week_ago = timezone.now() - timedelta(days=7)
        if self.value() == 'new':
            return queryset.filter(created_at__gte=week_ago)
        elif self.value() == 'old':
            return queryset.filter(created_at__lt=week_ago)
        return queryset


class HasPhotoFilter(SimpleListFilter):
    """Фильтр по наличию фотографий"""
    title = _('Фотографии')
    parameter_name = 'has_photos'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('С фото')),
            ('no', _('Без фото')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(photos__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(photos__isnull=True)
        return queryset


# ==============================
# INLINE МОДЕЛИ
# ==============================

class CarPhotoInline(admin.TabularInline):
    """Фотографии автомобиля"""
    model = CarPhoto
    extra = 0
    readonly_fields = ['photo_preview', 'thumbnail_preview']
    fields = ['image', 'photo_preview', 'thumbnail_preview', 'is_main', 'position', 'alt_text']

    def photo_preview(self, obj):
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 100px; max-width: 150px;" /></a>',
                obj.image.url, obj.image.url
            )
        return _("Нет фото")

    photo_preview.short_description = _('Превью')

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 50px; max-width: 80px;" /></a>',
                obj.thumbnail.url, obj.thumbnail.url
            )
        return _("Нет миниатюры")

    thumbnail_preview.short_description = _('Миниатюра')


class CarAdFeatureInline(admin.TabularInline):
    """Характеристики автомобиля"""
    model = CarAdFeature
    extra = 1
    autocomplete_fields = ['feature']
    fields = ['feature', 'value']
    verbose_name = _('Характеристика')
    verbose_name_plural = _('Характеристики')


# ==============================
# ДЕЙСТВИЯ АДМИНКИ
# ==============================

@admin.action(description=_('Активировать выбранные объявления'))
def activate_ads(modeladmin, request, queryset):
    """Активация объявлений"""
    updated = queryset.update(
        status='active',
        is_active=True,
        moderated_at=timezone.now(),
        moderator=request.user
    )
    modeladmin.message_user(
        request,
        _('{} объявлений активировано').format(updated)
    )


@admin.action(description=_('Отправить на модерацию'))
def send_for_moderation(modeladmin, request, queryset):
    """Отправка на модерацию"""
    updated = queryset.update(status='pending')
    modeladmin.message_user(
        request,
        _('{} объявлений отправлено на модерацию').format(updated)
    )


@admin.action(description=_('Пометить как проданные'))
def mark_as_sold(modeladmin, request, queryset):
    """Пометка как проданных"""
    updated = queryset.update(status='sold', is_active=False)
    modeladmin.message_user(
        request,
        _('{} объявлений помечено как проданные').format(updated)
    )


@admin.action(description=_('Заблокировать объявления'))
def ban_ads(modeladmin, request, queryset):
    """Блокировка объявлений"""
    updated = queryset.update(
        status='banned',
        is_active=False,
        moderated_at=timezone.now(),
        moderator=request.user
    )
    modeladmin.message_user(
        request,
        _('{} объявлений заблокировано').format(updated)
    )


@admin.action(description=_('Удалить старые фотографии без миниатюр'))
def generate_thumbnails(modeladmin, request, queryset):
    """Генерация миниатюр для фотографий"""
    from django.core.files.base import ContentFile
    from PIL import Image
    import io

    count = 0
    for photo in queryset.filter(thumbnail__isnull=True):
        try:
            # Открываем изображение
            img = Image.open(photo.image)

            # Создаем миниатюру
            img.thumbnail((300, 300))

            # Сохраняем в буфер
            thumb_io = io.BytesIO()
            img.save(thumb_io, format=img.format or 'JPEG')

            # Сохраняем в поле thumbnail
            thumb_file = ContentFile(thumb_io.getvalue())
            photo.thumbnail.save(
                f'thumb_{photo.image.name}',
                thumb_file,
                save=False
            )
            photo.save()
            count += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                _('Ошибка при обработке фото {}: {}').format(photo.id, str(e)),
                level='error'
            )

    modeladmin.message_user(
        request,
        _('Создано {} миниатюр').format(count)
    )


# ==============================
# МОДЕЛЬНЫЕ АДМИНЫ
# ==============================

@admin.register(CarAd)
class CarAdAdmin(admin.ModelAdmin):
    """Админка для объявлений о продаже автомобилей"""

    # Поля для отображения в списке
    list_display = [
        'id',
        'title_with_link',
        'owner_link',
        'brand_model_year',
        'price_formatted',
        'city_region',
        'status_badge',
        'views_count_display',
        'photos_count',
        'created_at_formatted',
        'is_active_badge',
    ]

    list_display_links = ['id', 'title_with_link']
    list_per_page = 25
    list_max_show_all = 100

    # Фильтры
    list_filter = [
        StatusFilter,
        OwnerTypeFilter,
        NewAdsFilter,
        HasPhotoFilter,
        'condition',
        'fuel_type',
        'transmission_type',
        'drive_type',
        'model__brand',
        'model',
        'city',
        'region',
        'is_negotiable',
        'has_tuning',
        'service_history',
        'created_at',
        'moderated_at',
    ]

    # Поиск
    search_fields = [
        'title',
        'description',
        'vin',
        'owner__username',
        'owner__email',
        'owner__first_name',
        'owner__last_name',
        'model__name',
        'model__brand__name',
        'city',
        'region',
    ]

    @admin.action(description=_('Перегенерировать заголовки'))
    def regenerate_titles(self, request, queryset):
        """Перегенерировать заголовки для выбранных объявлений"""
        count = 0
        for ad in queryset:
            # Генерируем новый заголовок
            new_title = ad.generate_title()
            if new_title != ad.title:
                ad.title = new_title
                ad.save(update_fields=['title'])
                count += 1

        if count > 0:
            self.message_user(
                request,
                _('Заголовки перегенерированы для {} объявлений').format(count),
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                _('Нет объявлений для перегенерации заголовков'),
                messages.WARNING
            )

    # Действия
    actions = [
        regenerate_titles,
        activate_ads,
        send_for_moderation,
        mark_as_sold,
        ban_ads,
    ]

    # Inline модели
    inlines = [CarPhotoInline, CarAdFeatureInline]

    # Группировка полей в форме редактирования
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'title',
                'slug',
                'description',
                'status',
                'is_active',
            )
        }),
        (_('Автомобиль'), {
            'fields': (
                'model',
                'brand',
                'year',
                'vin',
                'condition',
                ('mileage', 'mileage_unit'),
            )
        }),
        (_('Цена'), {
            'fields': (
                ('price', 'price_currency'),
                'is_negotiable',
            )
        }),
        (_('Технические характеристики'), {
            'fields': (
                ('engine_volume', 'engine_power'),
                ('fuel_type', 'transmission_type', 'drive_type'),
            )
        }),
        (_('Внешний вид'), {
            'fields': (
                'color',
                ('color_exterior', 'color_interior'),
                ('seats', 'doors'),
                'steering_wheel',
            )
        }),
        (_('Дополнительно'), {
            'fields': (
                'has_tuning',
                'service_history',
            )
        }),
        (_('Владелец'), {
            'fields': (
                'owner_type',
                'owner',
            )
        }),
        (_('Локация'), {
            'fields': (
                ('city', 'region'),
            )
        }),
        (_('Статистика'), {
            'fields': (
                'views',
                'views_count',
                'is_new',
            ),
            'classes': ('collapse',),
        }),
        (_('Системная информация'), {
            'fields': (
                'created_at',
                'modified_at',
                'moderated_at',
                'moderator',
            ),
            'classes': ('collapse',),
        }),
    )

    # Только для чтения
    readonly_fields = [
        'slug',
        'views',
        'views_count',
        'is_new',
        'created_at',
        'moderator',
    ]

    # Автозаполнение
    prepopulated_fields = {'slug': ('title',)}

    # Автозаполнение полей
    def save_model(self, request, obj, form, change):
        if not obj.moderator and obj.status == 'active':
            obj.moderator = request.user
            obj.moderated_at = timezone.now()
        super().save_model(request, obj, form, change)

    # Кастомные методы для list_display
    def title_with_link(self, obj):
        """Заголовок с ссылкой на сайт"""
        url = reverse('advertisements:ad_detail', kwargs={'slug': obj.slug})
        return format_html(
            '<a href="{}" target="_blank" title="{}">{}</a>',
            url,
            obj.title,
            obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
        )

    title_with_link.short_description = _('Заголовок')
    title_with_link.admin_order_field = 'title'

    def owner_link(self, obj):
        """Ссылка на владельца"""
        if obj.owner:
            url = reverse('admin:users_user_change', args=[obj.owner.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.owner.get_full_name() or obj.owner.username
            )
        return _('Нет владельца')

    owner_link.short_description = _('Владелец')
    owner_link.admin_order_field = 'owner__username'

    def brand_model_year(self, obj):
        """Марка, модель, год"""
        if obj.model:
            return f'{obj.model.brand.name} {obj.model.name} ({obj.year})'
        return f'{obj.year}'

    brand_model_year.short_description = _('Автомобиль')
    brand_model_year.admin_order_field = 'model__brand__name'

    def price_formatted(self, obj):
        """Отформатированная цена"""
        if obj.is_negotiable:
            return format_html(
                '<span style="color: #e67e22;">{} {}</span> <small>(торг)</small>',
                f'{obj.price:,.0f}'.replace(',', ' '),
                obj.get_price_currency_display()
            )
        return format_html(
            '<strong>{} {}</strong>',
            f'{obj.price:,.0f}'.replace(',', ' '),
            obj.get_price_currency_display()
        )

    price_formatted.short_description = _('Цена')
    price_formatted.admin_order_field = 'price'

    def city_region(self, obj):
        """Город и регион"""
        return f'{obj.city}, {obj.region}' if obj.region else obj.city

    city_region.short_description = _('Локация')
    city_region.admin_order_field = 'city'

    def status_badge(self, obj):
        """Бейдж статуса"""
        colors = {
            'active': 'success',
            'draft': 'secondary',
            'pending': 'warning',
            'sold': 'info',
            'expired': 'dark',
            'banned': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = _('Статус')
    status_badge.admin_order_field = 'status'

    def is_active_badge(self, obj):
        """Бейдж активности"""
        if obj.is_active:
            return format_html(
                '<span class="badge bg-success">✓</span>'
            )
        return format_html(
            '<span class="badge bg-danger">✗</span>'
        )

    is_active_badge.short_description = _('Акт.')

    def views_count_display(self, obj):
        """Количество просмотров"""
        return obj.views_count or obj.views

    views_count_display.short_description = _('Просм.')
    views_count_display.admin_order_field = 'views_count'

    def photos_count(self, obj):
        """Количество фотографий"""
        count = obj.photos.count()
        if count > 0:
            return format_html(
                '<span class="badge bg-info">{}</span>',
                count
            )
        return format_html(
            '<span class="badge bg-secondary">0</span>'
        )

    photos_count.short_description = _('Фото')

    def created_at_formatted(self, obj):
        """Форматированная дата создания"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    created_at_formatted.short_description = _('Создано')
    created_at_formatted.admin_order_field = 'created_at'

    # Кастомный queryset
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            'model__brand',
            'owner',
            'moderator'
        ).prefetch_related('photos').annotate(
            photos_count=Count('photos')
        )
        return queryset


@admin.register(CarPhoto)
class CarPhotoAdmin(admin.ModelAdmin):
    """Админка для фотографий автомобилей"""

    list_display = [
        'id',
        'car_ad_link',
        'photo_preview_list',
        'thumbnail_preview_list',
        'is_main_badge',
        'position',
        'created_at',
    ]

    list_display_links = ['id', 'car_ad_link']
    list_filter = ['is_main', 'car_ad__model__brand', 'created_at']
    search_fields = [
        'car_ad__title',
        'car_ad__vin',
        'car_ad__model__name',
        'car_ad__model__brand__name',
    ]
    actions = [generate_thumbnails]

    fields = [
        'car_ad',
        'image',
        'photo_preview',
        'thumbnail',
        'thumbnail_preview',
        'is_main',
        'position',
        'alt_text',
        'created_at',
        'modified_at',
    ]

    readonly_fields = [
        'photo_preview',
        'thumbnail_preview',
        'created_at',
    ]

    def car_ad_link(self, obj):
        """Ссылка на объявление"""
        url = reverse('admin:advertisements_carad_change', args=[obj.car_ad.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            f'{obj.car_ad.title[:40]}...' if len(obj.car_ad.title) > 40 else obj.car_ad.title
        )

    car_ad_link.short_description = _('Объявление')
    car_ad_link.admin_order_field = 'car_ad__title'

    def photo_preview_list(self, obj):
        """Превью фото в списке"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px;" />',
                obj.image.url
            )
        return _("Нет")

    photo_preview_list.short_description = _('Фото')

    def thumbnail_preview_list(self, obj):
        """Превью миниатюры в списке"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 30px; max-width: 50px;" />',
                obj.thumbnail.url
            )
        return _("Нет")

    thumbnail_preview_list.short_description = _('Миниатюра')

    def is_main_badge(self, obj):
        """Бейдж главной фотографии"""
        if obj.is_main:
            return format_html('<span class="badge bg-success">Главная</span>')
        return format_html('<span class="badge bg-secondary">Нет</span>')

    is_main_badge.short_description = _('Главная')

    def photo_preview(self, obj):
        """Превью фото в форме"""
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 300px; max-width: 400px;" /></a>',
                obj.image.url, obj.image.url
            )
        return _("Фото не загружено")

    photo_preview.short_description = _('Превью фото')

    def thumbnail_preview(self, obj):
        """Превью миниатюры в форме"""
        if obj.thumbnail:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 150px; max-width: 200px;" /></a>',
                obj.thumbnail.url, obj.thumbnail.url
            )
        return _("Миниатюра не создана")

    thumbnail_preview.short_description = _('Превью миниатюры')

    def save_model(self, request, obj, form, change):
        # Автоматически создаем миниатюру при загрузке
        if not obj.thumbnail and obj.image:
            # Можно добавить автоматическое создание миниатюр
            pass
        super().save_model(request, obj, form, change)


@admin.register(CarAdFeature)
class CarAdFeatureAdmin(admin.ModelAdmin):
    """Админка для характеристик объявлений"""

    list_display = [
        'id',
        'car_ad_link',
        'feature_name',
        'value',
        'created_at',
    ]

    list_filter = ['feature', 'car_ad__model__brand', 'created_at']
    search_fields = [
        'car_ad__title',
        'feature__name',
        'value',
    ]

    autocomplete_fields = ['car_ad', 'feature']

    def car_ad_link(self, obj):
        """Ссылка на объявление"""
        url = reverse('admin:advertisements_carad_change', args=[obj.car_ad.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            f'{obj.car_ad.title[:30]}...' if len(obj.car_ad.title) > 30 else obj.car_ad.title
        )

    car_ad_link.short_description = _('Объявление')
    car_ad_link.admin_order_field = 'car_ad__title'

    def feature_name(self, obj):
        return obj.feature.name

    feature_name.short_description = _('Характеристика')
    feature_name.admin_order_field = 'feature__name'


# @admin.register(FavoriteAd)
# class FavoriteAdAdmin(admin.ModelAdmin):
#     """Админка для избранных объявлений"""
#
#     list_display = [
#         'id',
#         'user_link',
#         'car_ad_link',
#         'created_at',
#     ]
#
#     list_filter = ['created_at']
#     search_fields = [
#         'user__username',
#         'user__email',
#         'car_ad__title',
#         'car_ad__vin',
#     ]
#
#     def user_link(self, obj):
#         """Ссылка на пользователя"""
#         if obj.user:
#             url = reverse('admin:users_user_change', args=[obj.user.id])
#             return format_html(
#                 '<a href="{}">{}</a>',
#                 url,
#                 obj.user.get_full_name() or obj.user.username
#             )
#         return _('Аноним')
#
#     user_link.short_description = _('Пользователь')
#     user_link.admin_order_field = 'user__username'
#
#     def car_ad_link(self, obj):
#         """Ссылка на объявление"""
#         url = reverse('admin:advertisements_carad_change', args=[obj.car_ad.id])
#         return format_html(
#             '<a href="{}">{}</a>',
#             url,
#             f'{obj.car_ad.title[:40]}...' if len(obj.car_ad.title) > 40 else obj.car_ad.title
#         )
#
#     car_ad_link.short_description = _('Объявление')
#     car_ad_link.admin_order_field = 'car_ad__title'


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """Админка для истории поиска"""

    list_display = [
        'id',
        'user_link',
        'search_query_short',
        'results_count',
        'created_at',
    ]

    list_filter = ['created_at']
    search_fields = [
        'search_query',
        'user__username',
        'user__email',
    ]

    readonly_fields = ['search_query_full', 'filters_display', 'created_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'search_query_full', 'filters_display', 'results_count')
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',),
        }),
    )

    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.user.get_full_name() or obj.user.username
            )
        return _('Аноним')

    user_link.short_description = _('Пользователь')
    user_link.admin_order_field = 'user__username'

    def search_query_short(self, obj):
        """Короткая версия поискового запроса"""
        if obj.search_query:
            return obj.search_query[:50] + '...' if len(obj.search_query) > 50 else obj.search_query
        return _('Без запроса')

    search_query_short.short_description = _('Поисковый запрос')

    def search_query_full(self, obj):
        """Полный поисковый запрос"""
        return obj.search_query or _('Нет запроса')

    search_query_full.short_description = _('Полный поисковый запрос')

    def filters_display(self, obj):
        """Отображение фильтров"""
        if obj.filters:
            filters_html = []
            for key, value in obj.filters.items():
                if value:  # Показываем только непустые значения
                    filters_html.append(f'<strong>{key}:</strong> {value}')
            return format_html('<br>'.join(filters_html))
        return _('Нет фильтров')

    filters_display.short_description = _('Фильтры')


@admin.register(CarView)
class CarViewAdmin(admin.ModelAdmin):
    """Админка для истории просмотров"""

    list_display = [
        'id',
        'user_link',
        'car_ad_link',
        'ip_address',
        'viewed_at',
    ]

    list_filter = ['viewed_at']
    search_fields = [
        'user__username',
        'user__email',
        'car_ad__title',
        'ip_address',
    ]

    readonly_fields = ['viewed_at', 'user_agent_display']

    fieldsets = (
        (None, {
            'fields': ('user', 'car_ad', 'ip_address', 'user_agent_display')
        }),
        (_('Системная информация'), {
            'fields': ('viewed_at',),
            'classes': ('collapse',),
        }),
    )

    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.user.get_full_name() or obj.user.username
            )
        return _('Аноним')

    user_link.short_description = _('Пользователь')
    user_link.admin_order_field = 'user__username'

    def car_ad_link(self, obj):
        """Ссылка на объявление"""
        url = reverse('admin:advertisements_carad_change', args=[obj.car_ad.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            f'{obj.car_ad.title[:40]}...' if len(obj.car_ad.title) > 40 else obj.car_ad.title
        )

    car_ad_link.short_description = _('Объявление')
    car_ad_link.admin_order_field = 'car_ad__title'

    def user_agent_display(self, obj):
        """Отображение User Agent"""
        return obj.user_agent or _('Не указан')

    user_agent_display.short_description = _('User Agent')


# ==============================
# ПАНЕЛЬ ИНСТРУМЕНТОВ АДМИНКИ
# ==============================

class AdvertisementAdminSite(admin.AdminSite):
    """Кастомная админка для объявлений"""
    site_header = _('Управление объявлениями Autoplaza')
    site_title = _('Админка Autoplaza')
    index_title = _('Панель управления объявлениями')

# Опционально: можно создать отдельную админку
# advertisement_admin = AdvertisementAdminSite(name='advertisement_admin')

# Регистрация стандартных моделей в основной админке
# (уже сделано через @admin.register)