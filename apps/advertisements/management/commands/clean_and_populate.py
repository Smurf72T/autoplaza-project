# apps/advertisements/management/commands/clean_and_populate.py
import os
import sys
import django
import random
import string
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Avg, Count  # ДОБАВИТЬ ЭТОТ ИМПОРТ
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.catalog.models import CarBrand, CarModel
from apps.advertisements.models import CarAd, CarPhoto, City, CarView, FavoriteAd, SearchHistory, CarAdFeature

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplaza.settings.development')
django.setup()


class Command(BaseCommand):
    help = 'Безопасная очистка и заполнение базы тестовыми объявлениями'

    # Данные для заполнения
    CITIES = [
        {'name': 'Москва', 'region': 'Московская область', 'slug': 'moscow'},
        {'name': 'Санкт-Петербург', 'region': 'Ленинградская область', 'slug': 'spb'},
        {'name': 'Казань', 'region': 'Татарстан', 'slug': 'kazan'},
        {'name': 'Екатеринбург', 'region': 'Свердловская область', 'slug': 'ekaterinburg'},
        {'name': 'Новосибирск', 'region': 'Новосибирская область', 'slug': 'novosibirsk'},
        {'name': 'Краснодар', 'region': 'Краснодарский край', 'slug': 'krasnodar'},
        {'name': 'Нижний Новгород', 'region': 'Нижегородская область', 'slug': 'nizhny-novgorod'},
        {'name': 'Ростов-на-Дону', 'region': 'Ростовская область', 'slug': 'rostov'},
        {'name': 'Сочи', 'region': 'Краснодарский край', 'slug': 'sochi'},
        {'name': 'Уфа', 'region': 'Башкортостан', 'slug': 'ufa'},
    ]

    DESCRIPTIONS = [
        "Автомобиль в отличном состоянии, полная сервисная история у дилера. Все ТО сделано вовремя, не бит, не крашен. Комплектация максимальная, есть все опции. Торг уместен.",
        "Продаю по причине переезда. Машина ухоженная, всегда в теплом гараже. Пробег реальный, подтвержден сервисной книжкой. Двигатель и коробка в идеальном состоянии.",
        "Срочная продажа, нужны деньги. Автомобиль в хорошем состоянии, мелкие царапины по кузову. Технически полностью исправен, готов к эксплуатации.",
        "Обмен на более крупный автомобиль. Участвовал в ДТП, восстановлен на официальном сервисе. Все документы на ремонт есть. Едет отлично.",
        "Автомобиль для семьи, все чеки на обслуживание сохранены. Интерьер чистый, без повреждений. Кондиционер, музыка, камера - все работает.",
        "Продаю второй автомобиль, мало езжу. Пробег небольшой, в основном по городу. Все жидкости заменены недавно. Зимняя резина в комплекте.",
        "Идеальный первый автомобиль. Экономичный, надежный. Все основные опции есть. Цена фиксированная, срочно.",
        "Авто с характером, ухожен как ребенок. Все работы только на оригинальных запчастях. Готов показать в любое время.",
        "Отличный вариант для города. Маневренный, экономичный. Недавно пройдено ТО, все в порядке. Обслуживался у официального дилера.",
        "Автомобиль в идеальном состоянии, один владелец. Всегда в закрытом паркинге. Полный пакет документов. Торг при осмотре.",
    ]

    EXTERIOR_COLORS = ['черный', 'белый', 'серебристый', 'серый', 'синий', 'красный', 'зеленый', 'коричневый', 'желтый',
                       'оранжевый']
    INTERIOR_COLORS = ['черный', 'бежевый', 'коричневый', 'серый', 'кремовый', 'красный']

    # Базовые цены для новых автомобилей (0 лет)
    BASE_PRICES = {
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

    TITLES = [
        "{brand} {model} {year} г.",
        "{brand} {model}, {year} год выпуска",
        "Продам {brand} {model} {year}",
        "{year} {brand} {model} в отличном состоянии",
        "{brand} {model} {year} - срочная продажа",
        "{brand} {model} {year}, низкий пробег",
        "Авто {brand} {model} {year} года",
        "{brand} {model}, {year}, полный комплект",
        "{brand} {model} {year} - идеальное состояние",
        "Срочно продаю {brand} {model} {year}",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Количество объявлений для создания (по умолчанию: 50)'
        )
        parser.add_argument(
            '--skip-clean',
            action='store_true',
            help='Пропустить очистку базы'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Email пользователя для создания объявлений'
        )

    def handle(self, *args, **options):
        """Основная логика команды"""

        if not options['skip_clean']:
            self.safe_clean_database()

        # Создаем города если их нет
        cities_dict = self.create_cities()

        # Получаем или создаем пользователя
        user = self.get_or_create_user(options.get('user'))
        if not user:
            self.stdout.write(self.style.ERROR('✗ Не удалось получить пользователя!'))
            return

        # Создаем объявления
        self.create_ads(
            count=options['count'],
            user=user,
            cities_dict=cities_dict
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Процесс завершен успешно!'
        ))

    def safe_clean_database(self):
        """Безопасная очистка базы данных через SQL"""
        self.stdout.write(self.style.WARNING('🔧 Начинаем безопасную очистку базы данных...'))

        try:
            with connection.cursor() as cursor:
                # Отключаем триггеры и проверки
                cursor.execute('SET session_replication_role = replica;')

                # Таблицы для очистки (в порядке зависимости)
                tables = [
                    'car_views',
                    'favorite_ads',
                    'search_history',
                    'car_ad_features',
                    'car_photos',
                    'car_ads',
                    'cities'
                ]

                cleaned_count = 0
                for table in tables:
                    try:
                        cursor.execute(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;')
                        cleaned_count += 1
                        self.stdout.write(f'  ✓ Очищена таблица: {table}')
                    except Exception as e:
                        # Если таблицы нет, пытаемся удалить записи если таблица существует
                        if 'не существует' in str(e) or 'does not exist' in str(e):
                            self.stdout.write(self.style.WARNING(f'  ⚠ Таблица {table} не существует, пропускаем'))
                        else:
                            # Пробуем DELETE вместо TRUNCATE
                            try:
                                cursor.execute(f'DELETE FROM {table};')
                                self.stdout.write(f'  ✓ Удалены записи из таблицы: {table}')
                                cleaned_count += 1
                            except:
                                self.stdout.write(self.style.WARNING(f'  ⚠ Не удалось очистить {table}'))

                # Включаем проверку обратно
                cursor.execute('SET session_replication_role = origin;')

                if cleaned_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ База данных очищена! Очищено таблиц: {cleaned_count}'))
                else:
                    self.stdout.write(self.style.WARNING('\n⚠ База данных уже пуста или не удалось очистить'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Ошибка очистки базы: {e}'))
            self.stdout.write(self.style.WARNING('Пробуем альтернативный способ...'))

            # Альтернативный способ - удалять через Django но без каскадов
            try:
                # Удаляем вручную, начиная с зависимых таблиц
                CarView.objects.all().delete()
                FavoriteAd.objects.all().delete()
                SearchHistory.objects.all().delete()
                CarAdFeature.objects.all().delete()
                CarPhoto.objects.all().delete()
                CarAd.objects.all().delete()
                City.objects.all().delete()

                self.stdout.write(self.style.SUCCESS('✅ База очищена альтернативным способом'))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'✗ Альтернативный способ тоже не сработал: {e2}'))
                self.stdout.write(self.style.WARNING('Продолжаем без очистки...'))

    def create_cities(self):
        """Создание городов"""
        self.stdout.write('\n🏙️  Создание городов...')
        cities_dict = {}

        for city_data in self.CITIES:
            try:
                city, created = City.objects.get_or_create(
                    slug=city_data['slug'],
                    defaults={
                        'name': city_data['name'],
                        'region': city_data['region'],
                        'country': 'Россия',
                        'is_active': True,
                        'is_major_city': True,
                    }
                )

                if created:
                    self.stdout.write(f'  ✓ Создан город: {city.name}')
                else:
                    self.stdout.write(f'  ↻ Город уже существует: {city.name}')

                cities_dict[city_data['name']] = city

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка создания города {city_data["name"]}: {e}'))

        return cities_dict

    def get_or_create_user(self, user_email=None):
        """Получаем или создаем тестового пользователя"""
        User = get_user_model()

        if user_email:
            try:
                user = User.objects.get(email=user_email)
                self.stdout.write(f'\n👤 Используем пользователя: {user.email}')
                return user
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'\n⚠ Пользователь {user_email} не найден'))

        # Берем первого пользователя
        try:
            user = User.objects.first()
            if user:
                self.stdout.write(f'\n👤 Используем существующего пользователя: {user.email}')
                return user
        except:
            pass

        # Создаем тестового пользователя
        try:
            user = User.objects.create_user(
                email='testuser@autoplaza.ru',
                phone='+7 (999) 123-45-67',
                first_name='Тестовый',
                last_name='Пользователь',
                password='TestPass123!'
            )
            self.stdout.write(self.style.SUCCESS(f'\n👤 Создан тестовый пользователь: {user.email}'))
            return user
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Ошибка создания пользователя: {e}'))

            # Пробуем взять любого пользователя
            try:
                user = User.objects.all()[0]
                self.stdout.write(f'👤 Используем пользователя: {user.email}')
                return user
            except:
                return None

    def create_ads(self, count, user, cities_dict):
        """Создание тестовых объявлений"""
        self.stdout.write(f'\n🚗 Создание {count} тестовых объявлений...')

        # Получаем все активные модели
        models = list(CarModel.objects.filter(is_active=True))
        if not models:
            self.stdout.write(self.style.ERROR('✗ Нет моделей в базе! Сначала заполните каталог.'))
            return

        ads_created = 0
        current_year = datetime.now().year

        # Список для отслеживания использованных VIN
        used_vins = set(CarAd.objects.exclude(vin__isnull=True).values_list('vin', flat=True))

        for i in range(count):
            try:
                with transaction.atomic():
                    # Выбираем случайную модель
                    model = random.choice(models)
                    brand = model.brand

                    # Генерируем год выпуска
                    min_year = max(2000, model.year_start or 2000)
                    max_year = min(current_year, model.year_end or current_year)
                    year = random.randint(min_year, max_year)

                    # Генерируем пробег
                    mileage = random.randint(10000, 300000)

                    # Генерируем цену
                    base_price = self.BASE_PRICES.get(brand.name, 1000000)
                    age = current_year - year

                    # Уменьшаем цену на 8-12% за каждый год
                    for _ in range(age):
                        depreciation = random.uniform(0.88, 0.92)
                        base_price *= depreciation

                    price_variation = random.randint(-50000, 50000)
                    price = int(base_price) + price_variation
                    price = max(100000, price)  # Минимальная цена 100к

                    # Выбираем город
                    city_name = random.choice(list(cities_dict.keys()))
                    city = cities_dict[city_name]

                    # Генерируем уникальный VIN (30% объявлений без VIN)
                    vin = None
                    if random.random() > 0.3:  # 70% с VIN
                        vin = self.generate_unique_vin(used_vins)
                        used_vins.add(vin)

                    # Генерируем уникальный slug
                    base_slug = slugify(f"{brand.name} {model.name} {year}")
                    counter = 1
                    slug = base_slug[:220]
                    while CarAd.objects.filter(slug=slug).exists():
                        slug = f"{base_slug[:215]}-{counter}"
                        counter += 1

                    # Выбираем состояние (чаще б/у)
                    condition_choices = ['used', 'used', 'used', 'used', 'new', 'salvage']
                    condition = random.choice(condition_choices)

                    # Выбираем тип владельца
                    owner_type = 'private' if random.random() > 0.2 else 'dealer'

                    # Создаем объявление
                    ad = CarAd.objects.create(
                        title=random.choice(self.TITLES).format(brand=brand.name, model=model.name, year=year),
                        slug=slug,
                        description=random.choice(self.DESCRIPTIONS),
                        price=price,
                        is_negotiable=random.choice([True, False]),
                        model=model,
                        brand=brand,
                        year=year,
                        vin=vin,
                        mileage=mileage,
                        mileage_unit='км',
                        engine_volume=random.choice([1.6, 1.8, 2.0, 2.5, 3.0, 3.5]),
                        engine_power=random.randint(100, 350),
                        fuel_type=random.choice(['petrol', 'diesel', 'hybrid', 'gas']),
                        transmission_type=random.choice(['manual', 'automatic', 'robot', 'variator']),
                        drive_type=random.choice(['front', 'rear', 'full', 'all_wheel']),
                        condition=condition,
                        color_exterior=random.choice(self.EXTERIOR_COLORS),
                        color_interior=random.choice(self.INTERIOR_COLORS),
                        city=city,
                        region=city.region,
                        seats=random.choice([4, 5, 7]),
                        doors=random.choice([2, 4, 5]),
                        steering_wheel='left',
                        has_tuning=random.random() > 0.8,  # 20% с тюнингом
                        service_history=random.random() > 0.3,  # 70% с историей
                        owner=user,
                        owner_type=owner_type,
                        status='active',
                        is_active=True,
                        views=random.randint(0, 500),
                        views_count=random.randint(0, 500),
                    )

                    ads_created += 1

                    # Выводим прогресс каждые 5 объявлений
                    if ads_created % 5 == 0:
                        self.stdout.write(f'  📝 Создано объявлений: {ads_created}')

                    # Выводим информацию о созданном объявлении
                    if ads_created <= 10 or ads_created % 10 == 0:
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ {ads_created:3d}. {brand.name} {model.name} {year} - {price:,}₽ ({city.name})'
                        ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка создания объявления {i + 1}: {str(e)[:100]}...'))
                continue

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Итого создано объявлений: {ads_created}'
        ))

        # Выводим статистику
        self.print_statistics()

    def generate_unique_vin(self, used_vins):
        """Генерирует уникальный VIN номер"""
        # Допустимые символы для VIN (без I, O, Q)
        letters = 'ABCDEFGHJKLMNPRSTUVWXYZ'
        digits = '0123456789'

        max_attempts = 100
        for _ in range(max_attempts):
            # Генерируем случайный VIN из 17 символов
            vin = ''.join(random.choice(letters + digits) for _ in range(17))

            # Проверяем уникальность
            if vin not in used_vins and not CarAd.objects.filter(vin=vin).exists():
                return vin

        # Если не удалось сгенерировать уникальный, возвращаем None
        return None

    def print_statistics(self):
        """Вывод статистики после создания"""
        total_ads = CarAd.objects.count()
        active_ads = CarAd.objects.filter(status='active', is_active=True).count()
        cities_count = City.objects.count()
        models_count = CarModel.objects.count()
        brands_count = CarBrand.objects.count()

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 СТАТИСТИКА БАЗЫ ДАННЫХ:')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Марок автомобилей: {brands_count}')
        self.stdout.write(f'  Моделей автомобилей: {models_count}')
        self.stdout.write(f'  Городов: {cities_count}')
        self.stdout.write(f'  Всего объявлений: {total_ads}')
        self.stdout.write(f'  Активных объявлений: {active_ads}')

        # Статистика по городам
        self.stdout.write('\n  📍 Объявления по городам:')
        from django.db.models import Count
        city_stats = CarAd.objects.values('city__name').annotate(count=Count('id')).order_by('-count')
        for stat in city_stats[:5]:
            city_name = stat['city__name'] or 'Не указан'
            self.stdout.write(f'    • {city_name}: {stat["count"]} объявлений')

        # Статистика по маркам
        self.stdout.write('\n  🚙 Популярные марки:')
        brand_stats = CarAd.objects.values('brand__name').annotate(count=Count('id')).order_by('-count')
        for stat in brand_stats[:5]:
            brand_name = stat['brand__name'] or 'Не указана'
            self.stdout.write(f'    • {brand_name}: {stat["count"]} объявлений')

        # Средняя цена
        avg_price = CarAd.objects.aggregate(avg=Avg('price'))['avg']  # ИСПРАВЛЕНО: models.Avg -> Avg
        if avg_price:
            self.stdout.write(f'\n  💰 Средняя цена: {int(avg_price):,}₽')

        self.stdout.write('=' * 50)