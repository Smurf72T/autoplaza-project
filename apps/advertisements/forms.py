# apps/advertisements/forms.py
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


class CarAdForm(forms.ModelForm):
    """Форма создания/редактирования объявления"""

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
        fields = [
            'title', 'description', 'price', 'is_negotiable',
            'year', 'vin', 'mileage', 'mileage_unit',
            'engine_volume', 'engine_power', 'fuel_type',
            'transmission_type', 'drive_type', 'condition',
            'color_exterior', 'color_interior', 'city', 'region',
            'seats', 'doors', 'steering_wheel', 'has_tuning', 'service_history'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткое описание',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Подробное описание автомобиля...',
                'maxlength': '5000'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2024'
            }),
            'vin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '17 символов',
                'maxlength': '17',
                'title': 'VIN должен содержать 17 символов (латинские буквы и цифры)'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000'
            }),
            'engine_volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.5',
                'max': '10.0'
            }),
            'engine_power': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '10'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Город'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Регион'
            }),
            'seats': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20'
            }),
            'doors': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2',
                'max': '6'
            }),
            'is_negotiable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_tuning': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'service_history': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
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

        # Настройка полей выбора с улучшенными атрибутами
        select_fields = [
            'fuel_type', 'transmission_type', 'drive_type',
            'condition', 'steering_wheel', 'mileage_unit'
        ]

        for field_name in select_fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-select',
                'data-choice': 'true'
            })

        # Делаем некоторые поля необязательными с улучшенными подсказками
        optional_fields = {
            'vin': {'required': False, 'help_text': 'Необязательно'},
            'engine_volume': {'required': False, 'help_text': 'л'},
            'engine_power': {'required': False, 'help_text': 'л.с.'},
            'seats': {'required': False, 'help_text': 'шт.'},
            'doors': {'required': False, 'help_text': 'шт.'},
            'color_exterior': {'required': False, 'help_text': 'Цвет кузова'},
            'color_interior': {'required': False, 'help_text': 'Цвет салона'},
        }

        for field_name, attrs in optional_fields.items():
            self.fields[field_name].required = attrs['required']
            if 'help_text' in attrs:
                self.fields[field_name].help_text = attrs['help_text']
                self.fields[field_name].widget.attrs['placeholder'] = attrs['help_text']

        # Добавляем валидаторы
        current_year = 2024
        self.fields['year'].validators.extend([
            MinValueValidator(1900),
            MaxValueValidator(current_year)
        ])

        self.fields['price'].validators.append(MinValueValidator(0))
        self.fields['mileage'].validators.append(MinValueValidator(0))

    def clean_vin(self):
        """Валидация VIN номера"""
        vin = self.cleaned_data.get('vin')
        if vin:
            vin = vin.upper().strip()
            # Проверка длины VIN
            if len(vin) != 17:
                raise forms.ValidationError('VIN должен содержать ровно 17 символов')
            # Проверка допустимых символов
            if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
                raise forms.ValidationError('VIN содержит недопустимые символы')
        return vin

    def clean_price(self):
        """Валидация цены"""
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной')
        return price

    def clean_mileage(self):
        """Валидация пробега"""
        mileage = self.cleaned_data.get('mileage')
        if mileage and mileage < 0:
            raise forms.ValidationError('Пробег не может быть отрицательным')
        return mileage

    def save(self, commit=True):
        """Переопределяем save для обработки поля brand"""
        # Сначала сохраняем модель CarAd без коммита
        car_ad = super().save(commit=False)

        # Устанавливаем brand из выбранной модели (автоматически будет через ForeignKey)
        # Или можно установить явно, если нужно:
        if car_ad.model and car_ad.model.brand:
            car_ad.brand = car_ad.model.brand

        if commit:
            car_ad.save()
            self.save_m2m()  # Если есть ManyToMany поля

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