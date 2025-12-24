# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Dealer, DealerReview
from .models_profile import Message, Notification, UserSettings, UserActivity
from ..advertisements.models import FavoriteAd


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_active', 'is_email_verified')
    list_filter = ('user_type', 'is_staff', 'is_active', 'is_email_verified', 'city')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        (_('Тип пользователя'), {'fields': ('user_type',)}),
        (_('Контактная информация'), {'fields': ('phone', 'city', 'about', 'birth_date')}),
        (_('Email подтверждение'),
         {'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        (_('Настройки уведомлений'), {'fields': ('receive_email_notifications', 'receive_sms_notifications')}),
        (_('Аватар'), {'fields': ('avatar',)}),
        (_('Активность'), {'fields': ('last_activity',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Дополнительная информация'), {'fields': ('user_type', 'phone', 'email')}),
    )
    readonly_fields = ('last_activity', 'date_joined')


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'city', 'is_verified', 'is_active', 'rating')
    list_filter = ('is_verified', 'is_active', 'city', 'region')
    search_fields = ('company_name', 'legal_name', 'user__username', 'user__email', 'phone')
    raw_id_fields = ('user',)
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('user', 'company_name', 'legal_name', 'description', 'logo')
        }),
        (_('Контактная информация'), {
            'fields': ('phone', 'email', 'website')
        }),
        (_('Адрес'), {
            'fields': ('address', 'city', 'region', 'postal_code', 'latitude', 'longitude')
        }),
        (_('Статус и рейтинг'), {
            'fields': ('is_verified', 'is_active', 'rating', 'reviews_count')
        }),
    )


@admin.register(DealerReview)
class DealerReviewAdmin(admin.ModelAdmin):
    list_display = ('dealer', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('dealer__company_name', 'user__username', 'comment')
    raw_id_fields = ('dealer', 'user')
    list_editable = ('is_approved',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'text_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'text')
    raw_id_fields = ('sender', 'recipient', 'ad')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Текст'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    raw_id_fields = ('user',)
    list_editable = ('is_read',)


@admin.register(FavoriteAd)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'car_ad', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'car_ad__title')
    raw_id_fields = ('user', 'car_ad')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'theme', 'show_phone')
    list_filter = ('language', 'theme', 'show_email', 'show_phone')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'ip_address', 'activity_type')
    raw_id_fields = ('user',)