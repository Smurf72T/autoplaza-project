# apps/reviews/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import TimeStampedModel, User


class Review(TimeStampedModel):
    """Отзывы пользователей"""

    class Rating(models.IntegerChoices):
        ONE = 1, '★☆☆☆☆'
        TWO = 2, '★★☆☆☆'
        THREE = 3, '★★★☆☆'
        FOUR = 4, '★★★★☆'
        FIVE = 5, '★★★★★'

    class ReviewType(models.TextChoices):
        SELLER_REVIEW = 'seller', _('Отзыв на продавца')
        BUYER_REVIEW = 'buyer', _('Отзыв на покупателя')
        DEALER_REVIEW = 'dealer', _('Отзыв на дилера')
        CAR_REVIEW = 'car', _('Отзыв на автомобиль')

    class Meta:
        db_table = 'reviews'
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        ordering = ['-created_at']
        unique_together = ['author', 'target_user', 'car_ad']

    # Участники
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_reviews',
        verbose_name=_('Автор')
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        verbose_name=_('Целевой пользователь')
    )

    # Контекст
    car_ad = models.ForeignKey(
        'advertisements.CarAd',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name=_('Объявление')
    )
    dealer = models.ForeignKey(
        'users.Dealer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dealer_reviews_list',
        verbose_name=_('Дилерский центр')
    )

    # Содержание
    rating = models.IntegerField(
        _('Рейтинг'),
        choices=Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)]  # Исправлено
    )
    title = models.CharField(_('Заголовок'), max_length=200)
    text = models.TextField(_('Текст отзыва'))
    review_type = models.CharField(
        _('Тип отзыва'),
        max_length=20,
        choices=ReviewType.choices,
        default=ReviewType.SELLER_REVIEW
    )

    # Верификация
    is_verified_purchase = models.BooleanField(_('Подтвержденная покупка'), default=False)
    is_approved = models.BooleanField(_('Одобрено'), default=False)
    is_edited = models.BooleanField(_('Редактировалось'), default=False)

    # Взаимодействия
    likes = models.IntegerField(_('Лайки'), default=0)
    dislikes = models.IntegerField(_('Дизлайки'), default=0)
    helpful_count = models.IntegerField(_('Полезно'), default=0)

    # Модерация
    moderator_comment = models.TextField(_('Комментарий модератора'), blank=True)

    def __str__(self):
        return f'Отзыв {self.author} → {self.target_user}: {self.rating}/5'

    def update_target_user_stats(self):
        """Обновить статистику целевого пользователя"""
        if self.is_approved and self.target_user:
            from django.db.models import Avg
            reviews = Review.objects.filter(
                target_user=self.target_user,
                is_approved=True
            )

            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
            count = reviews.count()

            self.target_user.profile.rating = avg_rating or 0
            self.target_user.profile.reviews_count = count
            self.target_user.profile.save(update_fields=['rating', 'reviews_count'])

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)

        if self.is_approved:
            self.update_target_user_stats()

    def delete(self, *args, **kwargs):
        target_user = self.target_user
        super().delete(*args, **kwargs)

        if target_user:
            # Нужно обновить метод update_target_user_stats чтобы он был статическим
            from django.db.models import Avg
            reviews = Review.objects.filter(
                target_user=target_user,
                is_approved=True
            )

            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
            count = reviews.count()

            target_user.profile.rating = avg_rating or 0
            target_user.profile.reviews_count = count
            target_user.profile.save(update_fields=['rating', 'reviews_count'])


class ReviewLike(TimeStampedModel):
    """Лайки/дизлайки отзывов"""

    class LikeType(models.TextChoices):
        LIKE = 'like', _('Нравится')
        DISLIKE = 'dislike', _('Не нравится')

    class Meta:
        db_table = 'review_likes'
        verbose_name = _('Лайк отзыва')
        verbose_name_plural = _('Лайки отзывов')
        unique_together = ['user', 'review']

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_likes',
        verbose_name=_('Пользователь')
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='likes_dislikes',
        verbose_name=_('Отзыв')
    )
    like_type = models.CharField(
        _('Тип реакции'),
        max_length=10,
        choices=LikeType.choices
    )

    def __str__(self):
        return f'{self.user} - {self.like_type} на отзыв {self.review.id}'


class ReviewHelpful(TimeStampedModel):
    """Отметки "Полезно" для отзывов"""

    class Meta:
        db_table = 'review_helpful'
        verbose_name = _('Полезный отзыв')
        verbose_name_plural = _('Полезные отзывы')
        unique_together = ['user', 'review']

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='helpful_reviews',
        verbose_name=_('Пользователь')
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_marks',
        verbose_name=_('Отзыв')
    )

    def __str__(self):
        return f'{self.user} отметил как полезный {self.review.id}'


class ReviewReply(TimeStampedModel):
    """Ответы на отзывы"""

    class Meta:
        db_table = 'review_replies'
        verbose_name = _('Ответ на отзыв')
        verbose_name_plural = _('Ответы на отзывы')

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_('Отзыв')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_replies',
        verbose_name=_('Автор')
    )
    text = models.TextField(_('Текст ответа'))
    is_edited = models.BooleanField(_('Редактировался'), default=False)

    def __str__(self):
        return f'Ответ на отзыв {self.review.id}'