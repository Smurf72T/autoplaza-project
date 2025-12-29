# apps/advertisements/forms.py
import datetime
import re
from decimal import Decimal

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import CarAd, CarPhoto
from apps.catalog.models import CarBrand, CarModel


# Кастомный виджет для множественной загрузки файлов
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        super().__init__(attrs)


class SimpleCarAdForm(forms.ModelForm):
    """Упрощенная форма создания объявления с минимальным набором полей"""

    brand = forms.ModelChoiceField(
        queryset=CarBrand.objects.filter(is_active=True),
        label='Марка',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_brand',
        })
    )

    model = forms.ModelChoiceField(
        queryset=CarModel.objects.none(),
        label='Модель',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_model',
        })
    )

    photos = forms.FileField(
        label='Фотографии',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = CarAd
        fields = [
            # Основные поля из шаблона
            'price', 'year', 'mileage', 'mileage_unit',
            'engine_volume', 'engine_power',
            'fuel_type', 'transmission_type', 'drive_type',
            'condition', 'steering_wheel', 'doors',
            'color_exterior', 'color_interior', 'seats',
            'city', 'region', 'vin', 'photos',
            'has_tuning', 'service_history', 'is_negotiable',
            'description'
        ]
        widgets = {
            # 'title': forms.TextInput(attrs={
            #     'class': 'form-control',
            #     'placeholder': 'Например: Toyota Camry 2015'
            # }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000',
                'placeholder': '₽'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2024',
                'placeholder': 'Год выпуска'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'mileage_unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'engine_volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.5',
                'max': '10',
                'placeholder': '1.6'
            }),
            'engine_power': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '50',
                'max': '1000',
                'placeholder': '150'
            }),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'transmission_type': forms.Select(attrs={'class': 'form-select'}),
            'drive_type': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'steering_wheel': forms.Select(attrs={'class': 'form-select'}),
            'doors': forms.Select(attrs={'class': 'form-select'}),
            'color_exterior': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Черный'
            }),
            'color_interior': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Черный'
            }),
            'seats': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2',
                'max': '9',
                'placeholder': '5'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Москва'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Московская область',
            }),
            'vin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXXXXXXXXXXXXXXXX',
                'maxlength': '17'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите состояние автомобиля, особенности...'
            }),
            'has_tuning': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'service_history': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_negotiable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Установим значения по умолчанию
        self.fields['mileage_unit'].initial = 'км'
        self.fields['condition'].initial = 'used'
        self.fields['steering_wheel'].initial = 'left'
        self.fields['fuel_type'].initial = 'petrol'
        self.fields['transmission_type'].initial = 'automatic'
        self.fields['drive_type'].initial = 'front'
        self.fields['is_negotiable'].initial = False
        self.fields['has_tuning'].initial = False
        self.fields['service_history'].initial = False
        self.fields['region'].initial = 'Москва'
        self.fields['doors'].initial = 4
        self.fields['seats'].initial = 5

        # Установим начальное значение для brand, если редактируем существующее объявление
        if self.instance and self.instance.pk and self.instance.model:
            self.fields['brand'].initial = self.instance.model.brand
            self.fields['model'].queryset = CarModel.objects.filter(
                brand=self.instance.model.brand,
                is_active=True
            )
            self.fields['model'].initial = self.instance.model
        else:
            # При создании нового объявления
            self.fields['model'].queryset = CarModel.objects.none()

        # Динамически обновляем queryset для model при отправке формы
        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['model'].queryset = CarModel.objects.filter(
                    brand_id=brand_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                self.fields['model'].queryset = CarModel.objects.none()
        elif 'brand' in self.initial:
            # Если передано начальное значение для brand
            try:
                brand_id = int(self.initial.get('brand'))
                self.fields['model'].queryset = CarModel.objects.filter(
                    brand_id=brand_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                self.fields['model'].queryset = CarModel.objects.none()

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()

        # Проверяем, что выбранная модель принадлежит выбранному бренду
        brand = cleaned_data.get('brand')
        model = cleaned_data.get('model')

        if brand and model:
            if model.brand != brand:
                self.add_error('model', 'Выбранная модель не принадлежит выбранной марке')
        return cleaned_data

    def save(self, commit=True):
        # Сохраняем объект CarAd
        car_ad = super().save(commit=False)

        # Получаем данные из формы
        brand = self.cleaned_data.get('brand')
        model = self.cleaned_data.get('model')

        # photos = self.request.FILES.getlist('photos')
        # for i, photo in enumerate(photos):
        #     CarPhoto.objects.create(
        #         car_ad=self.object,
        #         image=photo,
        #         is_main=(i == 0),
        #         position=i
        #     )

        # Устанавливаем модель из формы
        if model:
            car_ad.model = model

        # Устанавливаем brand из выбранной модели
        if model and model.brand:
            car_ad.brand = model.brand
        elif brand:
            car_ad.brand = brand

        # Устанавливаем значения по умолчанию
        car_ad.price_currency = 'RUB'
        car_ad.owner_type = 'private'
        car_ad.status = 'draft'
        car_ad.is_active = True
        car_ad.is_new = True

        # Автогенерация заголовка, если пустой
        if not car_ad.title or car_ad.title.strip() == '':
            model = self.cleaned_data.get('model')
            year = self.cleaned_data.get('year')
            if model and year:
                car_ad.title = f"{model.brand.name} {model.name} {year}"
            else:
                car_ad.title = "Автомобиль"

        # Устанавливаем владельца из запроса
        if hasattr(self, 'request') and self.request.user.is_authenticated:
            car_ad.owner = self.request.user

        if commit:
            car_ad.save()

        return car_ad



class CarAdForm(forms.ModelForm):
    """Упрощенная форма создания/редактирования объявления"""

    # Дополнительное поле для марки (не сохраняется в модель, используется для фильтрации моделей)
    brand = forms.ModelChoiceField(
        queryset=CarBrand.objects.filter(is_active=True),
        label='Марка',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_brand',
            'data-model-target': 'brand'
        })
    )

    # Поле для модели (остается как ForeignKey)
    model = forms.ModelChoiceField(
        queryset=CarModel.objects.none(),  # Будет заполняться динамически
        label='Модель',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_model',
            'data-model-target': 'model'
        })
    )

    # Поля для загрузки фото
    photos = forms.FileField(
        label='Фотографии',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = CarAd
        # Указываем только поля модели, которые будут в форме
        # Поле 'brand' (дополнительное) не входит в модель, поэтому его нет в fields
        fields = SimpleCarAdForm.Meta.fields # ← используем те же поля
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2025'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Город'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Установить начальное значение для brand, если редактируем существующее объявление
        if self.instance and self.instance.pk and self.instance.model:
            self.fields['brand'].initial = self.instance.model.brand
            self.fields['model'].queryset = CarModel.objects.filter(
                brand=self.instance.model.brand,
                is_active=True
            )
        else:
            # При создании нового объявления
            self.fields['model'].queryset = CarModel.objects.none()

        # Динамически обновляем queryset для model при отправке формы
        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['model'].queryset = CarModel.objects.filter(
                    brand_id=brand_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                self.fields['model'].queryset = CarModel.objects.none()

    def save(self, commit=True):
        """Переопределяем save для установки значений по умолчанию"""
        car_ad = super().save(commit=False)
        
        # Устанавливаем значения по умолчанию для обязательных полей
        if not car_ad.title:
            car_ad.title = f"{car_ad.model.brand.name} {car_ad.model.name} {car_ad.year}"
        
        car_ad.price_currency = 'RUB'
        car_ad.mileage = 0
        car_ad.mileage_unit = 'км'
        car_ad.condition = 'used'
        car_ad.owner_type = 'private'
        car_ad.region = car_ad.city if car_ad.city else 'Москва'
        car_ad.steering_wheel = 'left'
        car_ad.has_tuning = False
        car_ad.service_history = False
        car_ad.is_negotiable = False
        car_ad.status = 'draft'
        car_ad.is_active = True
        car_ad.is_new = True
        
        # Устанавливаем brand из выбранной модели
        if car_ad.model and car_ad.model.brand:
            car_ad.brand = car_ad.model.brand
        
        if commit:
            car_ad.save()
            self.save_m2m()
        
        return car_ad


class CarAdSearchForm(forms.Form):
    """Форма поиска объявлений"""

    # Поиск по тексту
    search = forms.CharField(
        required=False,
        label='Поиск',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Марка, модель, ключевые слова...',
            'autocomplete': 'off'
        })
    )

    # Марка и модель
    brand = forms.ModelChoiceField(
        queryset=CarBrand.objects.filter(is_active=True),
        required=False,
        label='Марка',
        empty_label='Любая марка',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-search-target': 'brand'
        })
    )

    model = forms.ModelChoiceField(
        queryset=CarModel.objects.none(),
        required=False,
        label='Модель',
        empty_label='Любая модель',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-search-target': 'model',
            'disabled': 'disabled'
        })
    )

    # Цена
    min_price = forms.IntegerField(
        required=False,
        label='Цена от',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '₽',
            'min': '0'
        })
    )

    max_price = forms.IntegerField(
        required=False,
        label='Цена до',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '₽',
            'min': '0'
        })
    )

    # Год выпуска
    min_year = forms.IntegerField(
        required=False,
        label='Год от',
        min_value=1900,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Год',
            'min': '1900',
            'max': '2024'
        })
    )

    max_year = forms.IntegerField(
        required=False,
        label='Год до',
        min_value=1900,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Год',
            'min': '1900',
            'max': '2024'
        })
    )

    # Пробег
    min_mileage = forms.IntegerField(
        required=False,
        label='Пробег от',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'км',
            'min': '0'
        })
    )

    max_mileage = forms.IntegerField(
        required=False,
        label='Пробег до',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'км',
            'min': '0'
        })
    )

    # Технические характеристики
    fuel_type = forms.ChoiceField(
        choices=[('', 'Все виды топлива')] + list(CarAd.FuelType.choices),
        required=False,
        label='Топливо',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    transmission_type = forms.ChoiceField(
        choices=[('', 'Все коробки')] + list(CarAd.TransmissionType.choices),
        required=False,
        label='Коробка передач',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    drive_type = forms.ChoiceField(
        choices=[('', 'Все приводы')] + list(CarAd.DriveType.choices),
        required=False,
        label='Привод',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    condition = forms.ChoiceField(
        choices=[('', 'Любое состояние')] + list(CarAd.ConditionType.choices),
        required=False,
        label='Состояние',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    owner_type = forms.ChoiceField(
        choices=[('', 'Любой владелец')] + list(CarAd.OwnerType.choices),
        required=False,
        label='Тип владельца',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Дополнительные фильтры
    color_exterior = forms.CharField(
        required=False,
        label='Цвет кузова',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Любой цвет'
        })
    )

    with_photo = forms.BooleanField(
        required=False,
        label='Только с фото',
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    is_negotiable = forms.BooleanField(
        required=False,
        label='Торг уместен',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    # Сортировка
    sort_by = forms.ChoiceField(
        choices=[
            ('', 'Сортировка'),
            ('-created_at', 'Сначала новые'),
            ('created_at', 'Сначала старые'),
            ('-price', 'Дорогие'),
            ('price', 'Дешевые'),
            ('-year', 'Новые'),
            ('year', 'Старые'),
            ('mileage', 'С малым пробегом'),
            ('-views_count', 'Популярные'),
        ],
        required=False,
        label='Сортировка',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Динамически подгружаем модели при выборе марки
        brand_id = self.data.get('brand') if self.data else None

        if brand_id:
            try:
                brand_id = int(brand_id)
                self.fields['model'].queryset = CarModel.objects.filter(
                    brand_id=brand_id,
                    is_active=True
                )
                self.fields['model'].widget.attrs.pop('disabled', None)
            except (ValueError, TypeError):
                self.fields['model'].queryset = CarModel.objects.none()
        else:
            # Если марка не выбрана, поле модели отключено
            self.fields['model'].queryset = CarModel.objects.none()
            self.fields['model'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        """Валидация связанных полей"""
        cleaned_data = super().clean()

        # Проверка, что минимальная цена не больше максимальной
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')

        if min_price and max_price and min_price > max_price:
            self.add_error('min_price', 'Минимальная цена не может быть больше максимальной')
            self.add_error('max_price', 'Максимальная цена не может быть меньше минимальной')

        # Проверка года
        min_year = cleaned_data.get('min_year')
        max_year = cleaned_data.get('max_year')

        if min_year and max_year and min_year > max_year:
            self.add_error('min_year', 'Минимальный год не может быть больше максимального')
            self.add_error('max_year', 'Максимальный год не может быть меньше минимального')

        # Проверка пробега
        min_mileage = cleaned_data.get('min_mileage')
        max_mileage = cleaned_data.get('max_mileage')

        if min_mileage and max_mileage and min_mileage > max_mileage:
            self.add_error('min_mileage', 'Минимальный пробег не может быть больше максимального')
            self.add_error('max_mileage', 'Максимальный пробег не может быть меньше минимального')

        return cleaned_data