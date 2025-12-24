# apps/advertisements/forms.py
from django import forms
from .models import CarAd, CarPhoto
from apps.catalog.models import CarBrand, CarModel


class CarAdForm(forms.ModelForm):
    """Форма создания/редактирования объявления"""

    # Дополнительные поля для фильтрации моделей по марке
    brand = forms.ModelChoiceField(
        queryset=CarBrand.objects.filter(is_active=True),
        label='Марка',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_brand'
        })
    )

    model = forms.ModelChoiceField(
        queryset=CarModel.objects.filter(is_active=True),
        label='Модель',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_model'
        })
    )

    # Поля для загрузки фото
    photos = forms.FileField(
        label='Фотографии',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': 'image/*'
        })
    )

    class Meta:
        model = CarAd
        fields = [
            'title', 'description', 'price', 'is_negotiable',
            'brand', 'model', 'year', 'vin', 'mileage', 'mileage_unit',
            'engine_volume', 'engine_power', 'fuel_type',
            'transmission_type', 'drive_type', 'condition',
            'color_exterior', 'color_interior', 'city', 'region',
            'seats', 'doors', 'steering_wheel', 'has_tuning', 'service_history'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Краткое описание'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2024'}),
            'vin': forms.TextInput(attrs={'class': 'form-control'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'engine_volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'engine_power': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'doors': forms.NumberInput(attrs={'class': 'form-control', 'min': '2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Если редактируем существующее объявление
        if self.instance and self.instance.pk:
            if self.instance.model:
                self.fields['brand'].initial = self.instance.model.brand
                # Фильтруем модели по выбранной марке
                self.fields['model'].queryset = CarModel.objects.filter(
                    brand=self.instance.model.brand,
                    is_active=True
                )

        # Настройка полей выбора
        for field_name in ['fuel_type', 'transmission_type', 'drive_type',
                           'condition', 'steering_wheel', 'mileage_unit']:
            self.fields[field_name].widget.attrs.update({'class': 'form-select'})

        # Делаем некоторые поля необязательными
        self.fields['vin'].required = False
        self.fields['engine_volume'].required = False
        self.fields['engine_power'].required = False
        self.fields['seats'].required = False
        self.fields['doors'].required = False


class CarAdSearchForm(forms.Form):
    """Форма поиска объявлений"""

    # Поиск по тексту
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Марка, модель, ключевые слова...'
        })
    )

    # Марка и модель
    brand = forms.ModelChoiceField(
        queryset=CarBrand.objects.filter(is_active=True),
        required=False,
        label='Марка',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    model = forms.ModelChoiceField(
        queryset=CarModel.objects.filter(is_active=True),
        required=False,
        label='Модель',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Цена
    min_price = forms.IntegerField(
        required=False,
        label='Цена от',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '₽'})
    )

    max_price = forms.IntegerField(
        required=False,
        label='Цена до',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '₽'})
    )

    # Год выпуска
    min_year = forms.IntegerField(
        required=False,
        label='Год от',
        min_value=1900,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Год'})
    )

    max_year = forms.IntegerField(
        required=False,
        label='Год до',
        min_value=1900,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Год'})
    )

    # Пробег
    min_mileage = forms.IntegerField(
        required=False,
        label='Пробег от',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'км'})
    )

    max_mileage = forms.IntegerField(
        required=False,
        label='Пробег до',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'км'})
    )

    # Технические характеристики
    fuel_type = forms.ChoiceField(
        choices=[('', 'Все')] + list(CarAd.FuelType.choices),
        required=False,
        label='Топливо',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    transmission_type = forms.ChoiceField(
        choices=[('', 'Все')] + list(CarAd.TransmissionType.choices),
        required=False,
        label='Коробка передач',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    drive_type = forms.ChoiceField(
        choices=[('', 'Все')] + list(CarAd.DriveType.choices),
        required=False,
        label='Привод',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    condition = forms.ChoiceField(
        choices=[('', 'Все')] + list(CarAd.ConditionType.choices),
        required=False,
        label='Состояние',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    owner_type = forms.ChoiceField(
        choices=[('', 'Все')] + list(CarAd.OwnerType.choices),
        required=False,
        label='Тип владельца',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Сортировка
    sort_by = forms.ChoiceField(
        choices=[
            ('created_at', 'По дате добавления'),
            ('price', 'По цене'),
            ('year', 'По году выпуска'),
            ('mileage', 'По пробегу'),
            ('views_count', 'По популярности'),
        ],
        required=False,
        label='Сортировка',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    order = forms.ChoiceField(
        choices=[
            ('desc', 'По убыванию'),
            ('asc', 'По возрастанию'),
        ],
        required=False,
        label='Порядок',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Динамически подгружаем модели при выборе марки
        brand_id = self.data.get('brand') if self.data else None
        if brand_id:
            self.fields['model'].queryset = CarModel.objects.filter(
                brand_id=brand_id,
                is_active=True
            )