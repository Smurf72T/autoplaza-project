# apps/catalog/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CarBrand, CarModel, CarFeature


@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'body_type', 'year_start', 'year_end', 'is_active')
    list_filter = ('is_active', 'brand', 'body_type')
    search_fields = ('name', 'brand__name', 'description')
    autocomplete_fields = ['brand']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

    # Поле для отображения страны марки
    def get_country(self, obj):
        return obj.brand.get_country_display()

    get_country.short_description = _('Страна')
    get_country.admin_order_field = 'brand__country'


@admin.register(CarFeature)
class CarFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_filterable', 'position', 'created_at')
    list_filter = ('category', 'is_filterable')
    search_fields = ('name',)
    list_editable = ('position', 'is_filterable')
    ordering = ('category', 'position')
    readonly_fields = ('created_at', 'updated_at')