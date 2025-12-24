# api/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from apps.users.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Min, Max
from django.http import JsonResponse
from django.core.cache import cache

from apps.advertisements.models import CarAd, FavoriteAd as Favorite, City
from apps.catalog.models import CarBrand, CarModel

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    CarAdSerializer,
    CarAdCreateSerializer,
    CarAdDetailSerializer,
    CarBrandSerializer,
    CarModelSerializer,
    FavoriteSerializer,
    MessageSerializer,
    ReviewSerializer,
    CitySerializer,
    StatsSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================================
# USER VIEWSETS
# ============================================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    Админы могут управлять всеми пользователями, обычные пользователи - только своим профилем.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """
        Разрешения в зависимости от действия:
        - list, retrieve: любой аутентифицированный пользователь
        - create: любой (регистрация)
        - update, partial_update, destroy: только владелец или админ
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Админы видят всех пользователей, обычные пользователи - только себя.
        """
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Получение информации о текущем пользователе.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Обновление профиля текущего пользователя.
        """
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# BRAND VIEWSET
# ============================================================================

class BrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet для марок автомобилей.
    """
    queryset = CarBrand.objects.filter(is_active=True)
    serializer_class = CarBrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'country']
    ordering_fields = ['name', 'created_at', 'models_count']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(models_count=Count('models'))

        # Фильтрация по стране
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country=country)

        return queryset

    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        """
        Получение всех моделей для конкретной марки.
        """
        brand = self.get_object()
        models = CarModel.objects.filter(brand=brand, is_active=True)
        serializer = CarModelSerializer(models, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Статистика по марке.
        """
        brand = self.get_object()

        # Статистика объявлений
        ads_stats = CarAd.objects.filter(
            model__brand=brand,
            status='active',
            is_active=True
        ).aggregate(
            total_ads=Count('id'),
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )

        # Количество моделей
        models_count = CarModel.objects.filter(brand=brand, is_active=True).count()

        return Response({
            'brand': brand.name,
            'models_count': models_count,
            **ads_stats
        })


# ============================================================================
# MODEL VIEWSET
# ============================================================================

class ModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet для моделей автомобилей.
    """
    queryset = CarModel.objects.filter(is_active=True)
    serializer_class = CarModelSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'brand__name']
    ordering_fields = ['name', 'year_start', 'year_end']
    ordering = ['brand__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('brand')

        # Фильтры
        brand_id = self.request.query_params.get('brand_id', None)
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)

        body_type = self.request.query_params.get('body_type', None)
        if body_type:
            queryset = queryset.filter(body_type=body_type)

        min_year = self.request.query_params.get('min_year', None)
        if min_year:
            queryset = queryset.filter(year_start__gte=min_year)

        max_year = self.request.query_params.get('max_year', None)
        if max_year:
            queryset = queryset.filter(
                Q(year_end__lte=max_year) | Q(year_end__isnull=True)
            )

        return queryset

    @action(detail=True, methods=['get'])
    def ads(self, request, pk=None):
        """
        Получение всех объявлений для конкретной модели.
        """
        model = self.get_object()
        ads = CarAd.objects.filter(
            model=model,
            status='active',
            is_active=True
        ).select_related('owner', 'model', 'city')

        page = self.paginate_queryset(ads)
        if page is not None:
            serializer = CarAdSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CarAdSerializer(ads, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """
        Получение похожих моделей.
        """
        model = self.get_object()
        similar_models = CarModel.objects.filter(
            brand=model.brand,
            body_type=model.body_type,
            is_active=True
        ).exclude(id=model.id).select_related('brand')[:6]

        serializer = CarModelSerializer(similar_models, many=True)
        return Response(serializer.data)


# ============================================================================
# AD VIEWSET
# ============================================================================

class AdViewSet(viewsets.ModelViewSet):
    """
    ViewSet для объявлений об автомобилях.
    """
    queryset = CarAd.objects.filter(is_active=True)
    serializer_class = CarAdSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'model__name', 'model__brand__name']
    ordering_fields = ['price', 'year', 'mileage', 'created_at', 'views']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Используем разные сериализаторы в зависимости от действия.
        """
        if self.action == 'create':
            return CarAdCreateSerializer
        elif self.action == 'retrieve':
            return CarAdDetailSerializer
        return CarAdSerializer

    def get_permissions(self):
        """
        Разрешения в зависимости от действия.
        """
        if self.action in ['list', 'retrieve', 'search']:
            permission_classes = [AllowAny]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'owner', 'model', 'brand', 'city'
        ).prefetch_related('photos')

        # Фильтры
        brand_id = self.request.query_params.get('brand', None)
        if brand_id:
            queryset = queryset.filter(model__brand_id=brand_id)

        model_id = self.request.query_params.get('model', None)
        if model_id:
            queryset = queryset.filter(model_id=model_id)

        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        min_year = self.request.query_params.get('min_year', None)
        if min_year:
            queryset = queryset.filter(year__gte=min_year)

        max_year = self.request.query_params.get('max_year', None)
        if max_year:
            queryset = queryset.filter(year__lte=max_year)

        city_id = self.request.query_params.get('city', None)
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        """
        При создании объявления устанавливаем владельца.
        """
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Расширенный поиск объявлений.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Дополнительные фильтры для поиска
        query = request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(model__name__icontains=query) |
                Q(model__brand__name__icontains=query)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """
        Увеличение счетчика просмотров.
        """
        ad = self.get_object()
        ad.views += 1
        ad.save()
        return Response({'views': ad.views})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """
        Добавление/удаление объявления из избранного.
        """
        ad = self.get_object()
        user = request.user

        favorite, created = Favorite.objects.get_or_create(
            user=user,
            ad=ad,
            defaults={'is_active': True}
        )

        if not created:
            favorite.is_active = not favorite.is_active
            favorite.save()

        action = 'added to' if favorite.is_active else 'removed from'
        return Response({
            'status': 'success',
            'message': f'Ad {action} favorites',
            'is_favorite': favorite.is_active
        })


# ============================================================================
# FAVORITE VIEWSET
# ============================================================================

class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet для избранных объявлений пользователя.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('ad', 'ad__model', 'ad__brand', 'ad__city')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """
        Очистка всех избранных объявлений.
        """
        Favorite.objects.filter(user=request.user, is_active=True).update(is_active=False)
        return Response({'status': 'success', 'message': 'All favorites cleared'})


# ============================================================================
# API VIEWS
# ============================================================================

class AdSearchView(APIView):
    """
    API для расширенного поиска объявлений.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        brand_id = request.query_params.get('brand_id')
        model_id = request.query_params.get('model_id')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        min_year = request.query_params.get('min_year')
        max_year = request.query_params.get('max_year')
        city_id = request.query_params.get('city_id')
        body_type = request.query_params.get('body_type')

        queryset = CarAd.objects.filter(
            status='active',
            is_active=True
        ).select_related('owner', 'model', 'brand', 'city')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(model__name__icontains=query) |
                Q(model__brand__name__icontains=query)
            )

        if brand_id:
            queryset = queryset.filter(model__brand_id=brand_id)

        if model_id:
            queryset = queryset.filter(model_id=model_id)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if min_year:
            queryset = queryset.filter(year__gte=min_year)

        if max_year:
            queryset = queryset.filter(year__lte=max_year)

        if city_id:
            queryset = queryset.filter(city_id=city_id)

        if body_type:
            queryset = queryset.filter(model__body_type=body_type)

        # Пагинация
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        ads = queryset[start:end]

        serializer = CarAdSerializer(ads, many=True)

        return Response({
            'count': total_count,
            'next': end < total_count,
            'previous': page > 1,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class ModelsByBrandView(APIView):
    """
    API для получения моделей по марке.
    """
    permission_classes = [AllowAny]

    def get(self, request, brand_id):
        models = CarModel.objects.filter(
            brand_id=brand_id,
            is_active=True
        ).order_by('name')

        serializer = CarModelSerializer(models, many=True)
        return Response(serializer.data)


class CityListView(APIView):
    """
    API для получения списка городов.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cities = City.objects.filter(is_active=True).order_by('name')
        serializer = CitySerializer(cities, many=True)
        return Response(serializer.data)


class StatsView(APIView):
    """
    API для получения статистики.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cache_key = 'api_stats'
        stats = cache.get(cache_key)

        if not stats:
            # Общая статистика
            total_ads = CarAd.objects.filter(is_active=True, status='active').count()
            total_brands = CarBrand.objects.filter(is_active=True).count()
            total_models = CarModel.objects.filter(is_active=True).count()
            total_users = User.objects.filter(is_active=True).count()

            # Статистика цен
            price_stats = CarAd.objects.filter(
                is_active=True,
                status='active',
                price__isnull=False
            ).aggregate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price')
            )

            # Популярные марки
            popular_brands = CarBrand.objects.filter(
                is_active=True
            ).annotate(
                ads_count=Count('models__ads')
            ).order_by('-ads_count')[:5]

            # Последние объявления
            recent_ads = CarAd.objects.filter(
                is_active=True,
                status='active'
            ).order_by('-created_at')[:5]

            stats = {
                'total_ads': total_ads,
                'total_brands': total_brands,
                'total_models': total_models,
                'total_users': total_users,
                'price_stats': price_stats,
                'popular_brands': CarBrandSerializer(popular_brands, many=True).data,
                'recent_ads': CarAdSerializer(recent_ads, many=True).data,
            }

            cache.set(cache_key, stats, 300)  # Кэшируем на 5 минут

        return Response(stats)


class CustomAuthToken(ObtainAuthToken):
    """
    Кастомный View для получения токена с дополнительной информацией о пользователе.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
        })


# ============================================================================
# UTILITY API VIEWS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, ad_id):
    """
    Переключение избранного для объявления.
    """
    try:
        ad = CarAd.objects.get(id=ad_id, is_active=True)
    except CarAd.DoesNotExist:
        return Response({'error': 'Ad not found'}, status=404)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        ad=ad,
        defaults={'is_active': True}
    )

    if not created:
        favorite.is_active = not favorite.is_active
        favorite.save()

    action = 'added to' if favorite.is_active else 'removed from'
    return Response({
        'status': 'success',
        'message': f'Ad {action} favorites',
        'is_favorite': favorite.is_active
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_favorites(request):
    """
    Очистка всех избранных объявлений пользователя.
    """
    Favorite.objects.filter(user=request.user, is_active=True).update(is_active=False)
    return Response({'status': 'success', 'message': 'All favorites cleared'})


@api_view(['POST'])
@permission_classes([AllowAny])
def check_username(request):
    """
    Проверка доступности username.
    """
    username = request.data.get('username', '').strip()

    if not username:
        return Response({'error': 'Username is required'}, status=400)

    exists = User.objects.filter(username__iexact=username).exists()
    return Response({'available': not exists, 'username': username})


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email(request):
    """
    Проверка доступности email.
    """
    email = request.data.get('email', '').strip().lower()

    if not email:
        return Response({'error': 'Email is required'}, status=400)

    exists = User.objects.filter(email__iexact=email).exists()
    return Response({'available': not exists, 'email': email})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_photo(request):
    """
    Загрузка фотографии.
    """
    if 'photo' not in request.FILES:
        return Response({'error': 'No photo file provided'}, status=400)

    photo = request.FILES['photo']

    # Проверка размера файла (максимум 5MB)
    if photo.size > 5 * 1024 * 1024:
        return Response({'error': 'File size exceeds 5MB limit'}, status=400)

    # Проверка типа файла
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if photo.content_type not in allowed_types:
        return Response({'error': 'Invalid file type'}, status=400)

    # Здесь должна быть логика сохранения файла
    # Например: photo_model = AdPhoto.objects.create(photo=photo, uploaded_by=request.user)

    return Response({
        'status': 'success',
        'message': 'Photo uploaded successfully',
        'file_name': photo.name,
        'file_size': photo.size,
        'content_type': photo.content_type
    })