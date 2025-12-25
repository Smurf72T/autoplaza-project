# apps/advertisements/management/commands/populate_ads.py
import os
import django
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.catalog.models import CarBrand, CarModel
from apps.advertisements.models import CarAd, CarPhoto, City
from apps.users.models import User


class Command(BaseCommand):
    help = 'Создание тестовых объявлений о продаже автомобилей'

    # Тестовые города
    CITIES = [
        {'name': 'Москва', 'region': 'Московская область', 'slug': 'moscow'},
        {'name': 'Санкт-Петербург', 'region': 'Ленинградская область', 'slug': 'spb'},
        {'name': 'Казань', 'region': 'Татарстан', 'slug': 'kazan'},
        {'name': 'Екатеринбург', 'region': 'Свердловская область', 'slug': 'ekaterinburg'},
        {'name': 'Новосибирск', 'region': 'Новосибирская область', 'slug': 'novosibirsk'},
        {'name': 'Краснодар', 'region': 'Краснодарский край', 'slug': 'krasnodar'},
        {'name': 'Нижний Новгород', 'region': 'Нижегородская область', 'slug': 'nizhny-novgorod'},
        {'name': 'Ростов-на-Дону', 'region': 'Ростовская область', 'slug': 'rostov'},
    ]

    # Описания автомобилей
    DESCRIPTIONS = [
        "Автомобиль в отличном состоянии, полная сервисная история у дилера. Все ТО сделано вовремя, не бит, не крашен. Комплектация максимальная, есть все опции. Торг уместен.",
        "Продаю по причине переезда. Машина ухоженная, всегда в теплом гараже. Пробег реальный, подтвержден сервисной книжкой. Двигатель и коробка в идеальном состоянии.",
        "Срочная продажа, нужны деньги. Автомобиль в хорошем состоянии, мелкие царапины по кузову. Технически полностью исправен, готов к эксплуатации.",
        "Обмен на более крупный автомобиль. Участвовал в ДТП, восстановлен на официальном сервисе. Все документы на ремонт есть. Едет отлично.",
        "Автомобиль для семьи, все чеки на обслуживание сохранены. Интерьер чистый, без повреждений. Кондиционер, музыка, камера - все работает.",
        "Продаю второй автомобиль, мало езжу. Пробег небольшой, в основном по городу. Все жидкости заменены недавно. Зимняя резина в комплекте.",
        "Идеальный первый автомобиль. Экономичный, надежный. Все основные опции есть. Цена фиксированная, срочно.",
        "Авто с характером, ухожен как ребенок. Все работы только на оригинальных запчастях. Готов показать в любое время.",
    ]

    # Контактные телефоны
    PHONES = [
        "+7 (916) 123-45-67",
        "+7 (925) 234-56-78",
        "+7 (903) 345-67-89",
        "+7 (985) 456-78-90",
        "+7 (999) 567-89-01",
    ]

    # VIN номера (примеры)
    VINS = [
        "JTDKB20U087654321",
        "WDDHF8JB3EA123456",
        "WAUZZZ8V6KA012345",
        "ZFA22300005678901",
        "KMHJG35WP3U123456",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Количество объявлений для создания (по умолчанию: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие объявления'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Email пользователя для создания объявлений (по умолчанию: первый найденный)'
        )

    def handle(self, *args, **options):
        """Основная логика команды"""

        if options['clear']:
            self.clear_ads()

        # Создаем города если их нет
        cities_dict = self.create_cities()

        # Получаем или создаем пользователя
        user = self.get_or_create_user(options.get('user'))

        # Создаем объявления
        self.create_ads(
            count=options['count'],
            user=user,
            cities_dict=cities_dict
        )

        self.stdout.write(self.style.SUCCESS(
            f'✅ Создано тестовых объявлений!'
        ))

    def clear_ads(self):
        """Очистка объявлений безопасным способом"""
        self.stdout.write(self.style.WARNING('Очистка объявлений...'))

        try:
            # Сначала удаляем связанные объекты в правильном порядке
            from apps.advertisements.models import CarPhoto, CarAdFeature, FavoriteAd, CarView

            # Удаляем в обратном порядке зависимостей
            CarView.objects.all().delete()
            FavoriteAd.objects.all().delete()
            CarAdFeature.objects.all().delete()
            CarPhoto.objects.all().delete()

            # Теперь удаляем объявления
            CarAd.objects.all().delete()

            # Удаляем города (если они не используются в других местах)
            City.objects.all().delete()

            self.stdout.write(self.style.SUCCESS('Объявления очищены'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка очистки: {e}'))
            self.stdout.write(self.style.WARNING('Пробуем альтернативный способ...'))

            # Альтернативный способ - отключить проверки внешних ключей
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    # Отключаем проверку внешних ключей
                    cursor.execute('SET CONSTRAINTS ALL DEFERRED')
                    # Удаляем записи
                    CarAd.objects.all().delete()
                    City.objects.all().delete()
                    cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')
                self.stdout.write(self.style.SUCCESS('Объявления очищены (альтернативный способ)'))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'Альтернативный способ тоже не сработал: {e2}'))

    def create_cities(self):
        """Создание городов"""
        cities_dict = {}

        for city_data in self.CITIES:
            try:
                city, created = City.objects.get_or_create(
                    slug=city_data['slug'],
                    defaults={
                        'name': city_data['name'],
                        'region': city_data['region'],
                        'is_active': True
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Создан город: {city.name}'))
                else:
                    self.stdout.write(f'↻ Город уже существует: {city.name}')

                cities_dict[city_data['name']] = city

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Ошибка создания города: {e}'))

        return cities_dict

    def get_or_create_user(self, user_email=None):
        """Получаем или создаем тестового пользователя"""
        User = get_user_model()

        if user_email:
            try:
                user = User.objects.get(email=user_email)
                self.stdout.write(f'✓ Используем пользователя: {user.email}')
                return user
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ Пользователь {user_email} не найден'))

        # Берем первого пользователя или создаем тестового
        try:
            user = User.objects.first()
            if user:
                self.stdout.write(f'✓ Используем существующего пользователя: {user.email}')
                return user
        except:
            pass

        # Создаем тестового пользователя
        try:
            user = User.objects.create_user(
                email='test@example.com',
                phone='+7 (999) 123-45-67',
                first_name='Тестовый',
                last_name='Пользователь',
                password='testpass123'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Создан тестовый пользователь: {user.email}'))
            return user
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка создания пользователя: {e}'))
            return None

    def create_ads(self, count, user, cities_dict):
        """Создание тестовых объявлений"""
        ads_created = 0

        # Получаем все активные модели
        models = list(CarModel.objects.filter(is_active=True))
        if not models:
            self.stdout.write(self.style.ERROR('✗ Нет моделей в базе! Сначала заполните каталог.'))
            return

        # Список для отслеживания использованных VIN
        used_vins = set()

        for i in range(count):
            try:
                # Выбираем случайную модель
                model = random.choice(models)
                brand = model.brand

                # Генерируем год выпуска (от 2000 до текущего года)
                current_year = datetime.now().year
                min_year = max(2000, model.year_start or 2000)
                max_year = min(current_year, model.year_end or current_year)
                year = random.randint(min_year, max_year)

                # Генерируем пробег (от 10к до 300к км)
                mileage = random.randint(10000, 300000)

                # Генерируем цену в зависимости от марки и возраста
                base_price = self.get_base_price(brand.name, year)
                price = base_price + random.randint(-50000, 50000)

                # Выбираем город
                city_name = random.choice(list(cities_dict.keys()))
                city = cities_dict[city_name]

                # Генерируем уникальный VIN (30% объявлений без VIN)
                vin = ''
                if random.random() > 0.3:  # 70% с VIN
                    vin = self.generate_unique_vin(used_vins)
                    used_vins.add(vin)

                # Генерируем уникальный slug
                base_slug = slugify(f"{brand.name} {model.name} {year} {random.randint(1000, 9999)}")
                # Проверяем уникальность slug
                counter = 1
                slug = base_slug[:220]
                while CarAd.objects.filter(slug=slug).exists():
                    slug = f"{base_slug[:215]}-{counter}"
                    counter += 1

                # Создаем объявление
                ad = CarAd.objects.create(
                    title=self.generate_title(brand, model, year),
                    slug=slug,
                    description=random.choice(self.DESCRIPTIONS),
                    price=price,
                    is_negotiable=random.choice([True, False]),
                    model=model,
                    brand=brand,
                    year=year,
                    vin=vin,  # Уникальный или пустой
                    mileage=mileage,
                    mileage_unit='км',
                    engine_volume=random.choice([1.6, 2.0, 2.5, 3.0, 3.5]),
                    engine_power=random.randint(100, 300),
                    fuel_type=random.choice(['petrol', 'diesel', 'hybrid']),
                    transmission_type=random.choice(['manual', 'automatic', 'robot']),
                    drive_type=random.choice(['front', 'rear', 'full']),
                    condition=random.choice(['new', 'used', 'used']),  # Чаще б/у
                    color_exterior=random.choice(['черный', 'белый', 'серебристый', 'серый', 'синий', 'красный']),
                    color_interior=random.choice(['черный', 'бежевый', 'коричневый', 'серый']),
                    city=city,
                    region=city.region,
                    seats=random.choice([4, 5, 7]),
                    doors=random.choice([2, 4, 5]),
                    steering_wheel='left',
                    has_tuning=random.random() > 0.8,  # 20% с тюнингом
                    service_history=random.random() > 0.3,  # 70% с историей
                    owner=user,
                    owner_type='private',
                    status='active',
                    is_active=True,
                    views=random.randint(0, 500),
                    views_count=random.randint(0, 500),
                )

                ads_created += 1

                # Выводим прогресс
                if ads_created % 5 == 0:
                    self.stdout.write(f'Создано объявлений: {ads_created}')

                self.stdout.write(self.style.SUCCESS(
                    f'✓ Объявление {ads_created}: {brand.name} {model.name} {year} - {price:,}₽'
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Ошибка создания объявления: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'✅ Итого создано объявлений: {ads_created}'
        ))

    def generate_unique_vin(self, used_vins):
        """Генерирует уникальный VIN номер"""
        # Допустимые символы для VIN (без I, O, Q)
        letters = 'ABCDEFGHJKLMNPRSTUVWXYZ'
        digits = '0123456789'

        while True:
            # Генерируем случайный VIN из 17 символов
            vin = ''.join(random.choice(letters + digits) for _ in range(17))

            # Проверяем уникальность
            if vin not in used_vins and not CarAd.objects.filter(vin=vin).exists():
                return vin

    def get_base_price(self, brand_name, year):
        """Базовые цены в зависимости от марки и возраста"""
        current_year = datetime.now().year
        age = current_year - year

        # Базовые цены для новых автомобилей (0 лет)
        base_prices = {
            'Toyota': 1500000,
            'BMW': 3000000,
            'Mercedes-Benz': 3500000,
            'Audi': 2800000,
            'Volkswagen': 1200000,
            'Ford': 1100000,
            'Hyundai': 900000,
            'Kia': 850000,
            'Lada (ВАЗ)': 600000,
            'Skoda': 1000000,
            'Nissan': 1300000,
            'Honda': 1400000,
            'Mazda': 1250000,
            'Subaru': 1600000,
            'Lexus': 4000000,
            'Chevrolet': 1400000,
            'Renault': 800000,
            'Peugeot': 950000,
            'Citroën': 850000,
            'Opel': 900000,
            'Volvo': 2500000,
            'Mitsubishi': 1200000,
            'Jeep': 2000000,
            'Land Rover': 3500000,
            'Porsche': 5000000,
            'Tesla': 4500000,
            'Geely': 700000,
            'Chery': 650000,
            'Haval': 750000,
        }

        # Берем базовую цену или среднюю
        base = base_prices.get(brand_name, 1000000)

        # Уменьшаем цену на 8-12% за каждый год
        for i in range(age):
            depreciation = random.uniform(0.88, 0.92)
            base *= depreciation

        return int(base)

    def generate_title(self, brand, model, year):
        """Генерация заголовка объявления"""
        titles = [
            f"{brand.name} {model.name} {year} г.",
            f"{brand.name} {model.name}, {year} год выпуска",
            f"Продам {brand.name} {model.name} {year}",
            f"{year} {brand.name} {model.name} в отличном состоянии",
            f"{brand.name} {model.name} {year} - срочная продажа",
            f"{brand.name} {model.name} {year}, низкий пробег",
            f"Авто {brand.name} {model.name} {year} года",
            f"{brand.name} {model.name}, {year}, полный комплект",
        ]
        return random.choice(titles)