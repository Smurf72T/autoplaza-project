# api/serializers.py
from rest_framework import serializers
from apps.users.models import User
from django.contrib.auth.password_validation import validate_password
from apps.advertisements.models import CarAd, FavoriteAd as Favorite, City, CarPhoto as AdPhoto  # ИСПРАВЛЕНО
from apps.catalog.models import CarBrand, CarModel
from apps.chat.models import ChatMessage as Message
from apps.reviews.models import Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'date_joined', 'last_login', 'is_staff']
        read_only_fields = ['date_joined', 'last_login', 'is_staff']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2',
                  'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class CarBrandSerializer(serializers.ModelSerializer):
    models_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CarBrand
        fields = ['id', 'name', 'slug', 'country', 'description',
                  'logo', 'is_active', 'models_count', 'created_at']
        read_only_fields = ['slug', 'created_at']


class CarModelSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    brand_slug = serializers.CharField(source='brand.slug', read_only=True)

    class Meta:
        model = CarModel
        fields = ['id', 'name', 'slug', 'brand', 'brand_name', 'brand_slug',
                  'body_type', 'year_start', 'year_end', 'description',
                  'image', 'is_active', 'created_at']
        read_only_fields = ['slug', 'created_at']


class AdPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdPhoto  # Теперь это алиас для CarPhoto
        fields = ['id', 'image', 'thumbnail', 'is_main', 'position', 'alt_text', 'created_at']  # ИСПРАВЛЕНО поля
        read_only_fields = ['created_at']


class CarAdSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='model.brand.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    photos = AdPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = CarAd
        fields = ['id', 'title', 'slug', 'description', 'price', 'price_currency',  # ИСПРАВЛЕНО: price_currency вместо currency
                  'year', 'mileage', 'mileage_unit', 'transmission_type', 'fuel_type', 'color',  # ИСПРАВЛЕНО имена полей
                  'engine_volume', 'engine_power', 'drive_type', 'steering_wheel',
                  'condition', 'owner_type', 'vin',
                  'brand_name', 'model_name', 'city_name', 'owner_username',
                  'status', 'views', 'is_active', 'photos', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'views', 'created_at', 'updated_at']


class CarAdCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarAd
        fields = ['title', 'description', 'price', 'price_currency',
                  'model', 'year', 'mileage', 'mileage_unit', 'city', 'transmission_type',
                  'fuel_type', 'color', 'engine_volume',
                  'engine_power', 'drive_type', 'steering_wheel',
                  'condition', 'owner_type', 'vin']  # ИСПРАВЛЕНО имена полей


class CarAdDetailSerializer(CarAdSerializer):
    class Meta(CarAdSerializer.Meta):
        # Добавьте дополнительные поля для детального просмотра
        fields = CarAdSerializer.Meta.fields + ['contact_phone', 'contact_email']  # Если есть такие поля в модели


class FavoriteSerializer(serializers.ModelSerializer):
    ad = CarAdSerializer(read_only=True)
    ad_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'ad', 'ad_id', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'slug', 'region', 'country',
                  'latitude', 'longitude', 'population', 'ads_count', 'is_active']  # ОДИН класс, не дублируйте
        read_only_fields = ['slug']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'recipient', 'recipient_username',
                  'ad', 'content', 'is_read', 'created_at']
        read_only_fields = ['created_at']


class ReviewSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'author', 'author_username', 'ad', 'car_ad',
                  'rating', 'content', 'is_approved', 'review_type',
                  'created_at']
        read_only_fields = ['created_at']


class StatsSerializer(serializers.Serializer):
    total_ads = serializers.IntegerField()
    total_brands = serializers.IntegerField()
    total_models = serializers.IntegerField()
    total_users = serializers.IntegerField()
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)