# apps/reviews/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
from .models import Review, ReviewLike, ReviewHelpful, ReviewReply
from apps.users.models import User
from apps.advertisements.models import CarAd


class ReviewListView(ListView):
    """Список отзывов"""
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        queryset = Review.objects.filter(
            is_approved=True
        ).select_related(
            'author', 'target_user', 'car_ad__model__brand'
        ).order_by('-created_at')

        # Фильтры
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(target_user_id=user_id)

        rating = self.request.GET.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)

        review_type = self.request.GET.get('type')
        if review_type:
            queryset = queryset.filter(review_type=review_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика для фильтров
        if self.request.GET.get('user'):
            user_id = self.request.GET.get('user')
            user = get_object_or_404(User, id=user_id)

            # Средний рейтинг
            avg_rating = Review.objects.filter(
                target_user=user,
                is_approved=True
            ).aggregate(avg=Avg('rating'))['avg'] or 0

            # Распределение по оценкам
            rating_distribution = Review.objects.filter(
                target_user=user,
                is_approved=True
            ).values('rating').annotate(count=Count('id')).order_by('-rating')

            context['target_user'] = user
            context['avg_rating'] = round(avg_rating, 1)
            context['rating_distribution'] = rating_distribution

        return context


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Создание отзыва"""
    template_name = 'reviews/review_form.html'
    model = Review
    fields = ['rating', 'title', 'text', 'review_type']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем целевого пользователя из параметров
        target_user_id = self.request.GET.get('target_user')
        ad_id = self.request.GET.get('ad')

        if target_user_id:
            context['target_user'] = get_object_or_404(User, id=target_user_id)

        if ad_id:
            context['car_ad'] = get_object_or_404(CarAd, id=ad_id)

        return context

    def form_valid(self, form):
        # Устанавливаем автора
        form.instance.author = self.request.user

        # Устанавливаем целевого пользователя
        target_user_id = self.request.POST.get('target_user')
        if target_user_id:
            form.instance.target_user = get_object_or_404(User, id=target_user_id)

        # Устанавливаем объявление
        ad_id = self.request.POST.get('car_ad')
        if ad_id:
            form.instance.car_ad = get_object_or_404(CarAd, id=ad_id)

        # Проверяем, можно ли оставить отзыв
        # (например, только после завершенной сделки)

        messages.success(self.request, 'Отзыв отправлен на модерацию')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('reviews:review_detail', kwargs={'pk': self.object.pk})


class ReviewDetailView(DetailView):
    """Детали отзыва"""
    template_name = 'reviews/review_detail.html'
    model = Review
    context_object_name = 'review'

    def get_queryset(self):
        return Review.objects.filter(
            is_approved=True
        ).select_related(
            'author', 'target_user', 'car_ad__model__brand'
        ).prefetch_related('replies')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Проверяем, лайкнул ли пользователь этот отзыв
        if self.request.user.is_authenticated:
            context['user_like'] = ReviewLike.objects.filter(
                user=self.request.user,
                review=self.object
            ).first()

            context['is_helpful'] = ReviewHelpful.objects.filter(
                user=self.request.user,
                review=self.object
            ).exists()

        # Ответы на отзыв
        context['replies'] = self.object.replies.all().select_related('author')

        return context

class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование отзыва"""
    template_name = 'reviews/review_form.html'
    model = Review
    fields = ['rating', 'title', 'text', 'review_type']

    def get_queryset(self):
        # Пользователь может редактировать только свои отзывы
        return Review.objects.filter(author=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Отзыв обновлен')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('reviews:review_detail', kwargs={'pk': self.object.pk})


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление отзыва"""
    template_name = 'reviews/review_confirm_delete.html'
    model = Review

    def get_queryset(self):
        # Пользователь может удалять только свои отзывы
        return Review.objects.filter(author=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Отзыв удален')
        return reverse_lazy('reviews:review_list')


class UserReviewsView(ListView):
    """Отзывы о конкретном пользователе"""
    template_name = 'reviews/user_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        self.target_user = get_object_or_404(User, id=user_id)

        return Review.objects.filter(
            target_user=self.target_user,
            is_approved=True
        ).select_related(
            'author', 'target_user', 'car_ad__model__brand'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.target_user

        # Статистика
        avg_rating = Review.objects.filter(
            target_user=self.target_user,
            is_approved=True
        ).aggregate(avg=Avg('rating'))['avg'] or 0

        rating_distribution = Review.objects.filter(
            target_user=self.target_user,
            is_approved=True
        ).values('rating').annotate(count=Count('id')).order_by('-rating')

        context['avg_rating'] = round(avg_rating, 1)
        context['rating_distribution'] = rating_distribution

        return context


class AdReviewsView(ListView):
    """Отзывы на конкретное объявление"""
    template_name = 'reviews/ad_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        ad_id = self.kwargs.get('ad_id')
        self.car_ad = get_object_or_404(CarAd, id=ad_id)

        return Review.objects.filter(
            car_ad=self.car_ad,
            is_approved=True
        ).select_related(
            'author', 'target_user', 'car_ad__model__brand'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['car_ad'] = self.car_ad
        return context


class LikeReviewView(LoginRequiredMixin, View):
    """Лайк/дизлайк отзыва"""

    def post(self, request, *args, **kwargs):
        review_id = request.POST.get('review_id')
        like_type = request.POST.get('like_type')  # 'like' или 'dislike'

        review = get_object_or_404(Review, id=review_id)

        # Проверяем, не оставлял ли уже пользователь реакцию
        existing_like = ReviewLike.objects.filter(
            user=request.user,
            review=review
        ).first()

        if existing_like:
            # Если уже есть такая же реакция - удаляем
            if existing_like.like_type == like_type:
                existing_like.delete()

                # Обновляем счетчики
                if like_type == 'like':
                    review.likes -= 1
                else:
                    review.dislikes -= 1

                action = 'removed'
            else:
                # Меняем реакцию
                old_type = existing_like.like_type
                existing_like.like_type = like_type
                existing_like.save()

                # Обновляем счетчики
                if old_type == 'like':
                    review.likes -= 1
                    review.dislikes += 1
                else:
                    review.dislikes -= 1
                    review.likes += 1

                action = 'changed'
        else:
            # Создаем новую реакцию
            ReviewLike.objects.create(
                user=request.user,
                review=review,
                like_type=like_type
            )

            # Обновляем счетчики
            if like_type == 'like':
                review.likes += 1
            else:
                review.dislikes += 1

            action = 'added'

        review.save()

        return JsonResponse({
            'action': action,
            'likes': review.likes,
            'dislikes': review.dislikes,
            'like_type': like_type
        })


class MarkHelpfulView(LoginRequiredMixin, View):
    """Отметить отзыв как полезный"""

    def post(self, request, *args, **kwargs):
        review_id = request.POST.get('review_id')

        review = get_object_or_404(Review, id=review_id)

        # Проверяем, не отмечал ли уже пользователь
        existing = ReviewHelpful.objects.filter(
            user=request.user,
            review=review
        ).first()

        if existing:
            # Удаляем отметку
            existing.delete()
            review.helpful_count -= 1
            action = 'removed'
        else:
            # Добавляем отметку
            ReviewHelpful.objects.create(
                user=request.user,
                review=review
            )
            review.helpful_count += 1
            action = 'added'

        review.save()

        return JsonResponse({
            'action': action,
            'helpful_count': review.helpful_count
        })


class AddReplyView(LoginRequiredMixin, CreateView):
    """Добавление ответа на отзыв"""
    model = ReviewReply
    fields = ['text']

    def form_valid(self, form):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id)

        form.instance.review = review
        form.instance.author = self.request.user

        # Только целевой пользователь может отвечать на отзыв
        if review.target_user != self.request.user:
            messages.error(self.request, 'Вы не можете отвечать на этот отзыв')
            return redirect('reviews:review_detail', pk=review_id)

        messages.success(self.request, 'Ответ добавлен')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('reviews:review_detail', kwargs={'pk': self.object.review.pk})