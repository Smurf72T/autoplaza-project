# apps/analytics/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    PageView, SearchAnalytics, UserActivity,
    DailyStats, ConversionEvent
)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    """Админка для просмотров страниц"""

    list_display = [
        'id', 'short_page_url', 'user_info',
        'device_type', 'viewed_at', 'time_on_page'
    ]
    list_filter = [
        'device_type', 'browser', 'os',
        'viewed_at', 'car_ad', 'car_brand'
    ]
    search_fields = [
        'page_url', 'page_title', 'user__email',
        'user__first_name', 'user__last_name',
        'ip_address', 'session_id'
    ]
    readonly_fields = ['viewed_at']
    fieldsets = [
        (_('Основная информация'), {
            'fields': ['user', 'page_url', 'page_title', 'referrer']
        }),
        (_('Контекст'), {
            'fields': ['car_ad', 'car_brand', 'car_model'],
            'classes': ['collapse']
        }),
        (_('Техническая информация'), {
            'fields': [
                'ip_address', 'user_agent', 'session_id',
                'device_type', 'browser', 'os'
            ],
            'classes': ['collapse']
        }),
        (_('Время'), {
            'fields': ['viewed_at', 'time_on_page']
        }),
    ]

    def short_page_url(self, obj):
        """Сокращенный URL для отображения в списке"""
        if len(obj.page_url) > 50:
            return f'{obj.page_url[:50]}...'
        return obj.page_url

    short_page_url.short_description = _('URL страницы')

    def user_info(self, obj):
        """Информация о пользователе"""
        if obj.user:
            return f'{obj.user.email} ({obj.user.get_full_name() or "-"})'
        return _('Анонимный')

    user_info.short_description = _('Пользователь')


@admin.register(SearchAnalytics)
class SearchAnalyticsAdmin(admin.ModelAdmin):
    """Админка для аналитики поиска"""

    list_display = [
        'id', 'short_query', 'user_info',
        'results_count', 'has_results', 'searched_at'
    ]
    list_filter = ['has_results', 'searched_at']
    search_fields = [
        'query', 'user__email', 'user__first_name',
        'user__last_name', 'ip_address'
    ]
    readonly_fields = ['searched_at']
    fieldsets = [
        (_('Основная информация'), {
            'fields': ['user', 'query', 'filters']
        }),
        (_('Результаты'), {
            'fields': ['results_count', 'has_results', 'clicked_result']
        }),
        (_('Техническая информация'), {
            'fields': ['ip_address', 'session_id'],
            'classes': ['collapse']
        }),
        (_('Время'), {
            'fields': ['searched_at']
        }),
    ]

    def short_query(self, obj):
        """Сокращенный запрос для отображения в списке"""
        if len(obj.query) > 30:
            return f'{obj.query[:30]}...'
        return obj.query

    short_query.short_description = _('Запрос')

    def user_info(self, obj):
        """Информация о пользователе"""
        if obj.user:
            return f'{obj.user.email}'
        return _('Анонимный')

    user_info.short_description = _('Пользователь')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Админка для активности пользователей"""

    list_display = [
        'id', 'user_info', 'get_activity_type_display',
        'short_data', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'ip_address', 'data'
    ]
    readonly_fields = ['created_at']
    fieldsets = [
        (_('Основная информация'), {
            'fields': ['user', 'activity_type', 'data']
        }),
        (_('Контекст'), {
            'fields': ['car_ad', 'target_user'],
            'classes': ['collapse']
        }),
        (_('Техническая информация'), {
            'fields': ['ip_address', 'user_agent'],
            'classes': ['collapse']
        }),
    ]

    def short_data(self, obj):
        """Сокращенные данные активности"""
        if obj.data:
            data_str = str(obj.data)
            if len(data_str) > 50:
                return f'{data_str[:50]}...'
            return data_str
        return '-'

    short_data.short_description = _('Данные')

    def user_info(self, obj):
        """Информация о пользователе"""
        return f'{obj.user.email} ({obj.user.get_full_name() or "-"})'

    user_info.short_description = _('Пользователь')


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    """Админка для ежедневной статистики"""

    list_display = [
        'date', 'new_users', 'active_users',
        'new_ads', 'total_views', 'searches',
        'payments_amount', 'conversion_rate'
    ]
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (_('Дата'), {
            'fields': ['date']
        }),
        (_('Пользователи'), {
            'fields': ['new_users', 'active_users'],
            'classes': ['collapse']
        }),
        (_('Объявления'), {
            'fields': ['new_ads', 'active_ads', 'sold_ads'],
            'classes': ['collapse']
        }),
        (_('Просмотры'), {
            'fields': ['total_views', 'unique_views'],
            'classes': ['collapse']
        }),
        (_('Поиск'), {
            'fields': ['searches', 'popular_searches'],
            'classes': ['collapse']
        }),
        (_('Сообщения'), {
            'fields': ['messages_sent'],
            'classes': ['collapse']
        }),
        (_('Платежи'), {
            'fields': ['payments_amount', 'payments_count'],
            'classes': ['collapse']
        }),
        (_('Конверсии'), {
            'fields': ['conversion_rate'],
            'classes': ['collapse']
        }),
    ]

    def has_add_permission(self, request):
        """Запрещаем добавление вручную"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление"""
        return False


@admin.register(ConversionEvent)
class ConversionEventAdmin(admin.ModelAdmin):
    """Админка для событий конверсии"""

    list_display = [
        'id', 'user_info', 'get_event_type_display',
        'car_ad_info', 'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'car_ad__title', 'session_id'
    ]
    readonly_fields = ['created_at']
    fieldsets = [
        (_('Основная информация'), {
            'fields': ['user', 'car_ad', 'event_type']
        }),
        (_('Дополнительные данные'), {
            'fields': ['data', 'session_id'],
            'classes': ['collapse']
        }),
    ]

    def user_info(self, obj):
        """Информация о пользователе"""
        if obj.user:
            return f'{obj.user.email}'
        return _('Анонимный')

    user_info.short_description = _('Пользователь')

    def car_ad_info(self, obj):
        """Информация об объявлении"""
        if obj.car_ad:
            return f'{obj.car_ad.title}'
        return '-'

    car_ad_info.short_description = _('Объявление')


# Дополнительные настройки админки
admin.site.site_header = _('Аналитика сайта')
admin.site.site_title = _('Администрирование аналитики')
admin.site.index_title = _('Панель управления аналитикой')