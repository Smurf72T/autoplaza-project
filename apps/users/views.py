# apps/users/views.py
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, PasswordResetView
from django.views.generic import CreateView, UpdateView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .forms import CustomUserCreationForm, ProfileEditForm, CustomAuthenticationForm
from .models import User
from .models_profile import Message, Notification, UserSettings, UserActivity
from ..advertisements.models import FavoriteAd as Favorite


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)

        response = super().form_valid(form)

        # Обновляем активность
        user = form.get_user()
        user.update_last_activity()

        messages.success(self.request, f'Добро пожаловать, {user.username}!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        return context


class RegisterView(CreateView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)

        # Обновляем активность
        user.update_last_activity()

        # Отправляем email для подтверждения
        try:
            user.send_email_verification()
            messages.info(self.request, 'На ваш email отправлено письмо для подтверждения.')
        except Exception as e:
            messages.warning(self.request, f'Не удалось отправить письмо для подтверждения: {str(e)}')

        # Создаем активность
        UserActivity.objects.create(
            user=user,
            activity_type='registration',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

        messages.success(self.request, 'Регистрация прошла успешно!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cities'] = [
            ('moscow', 'Москва'),
            ('saint-petersburg', 'Санкт-Петербург'),
            ('ekaterinburg', 'Екатеринбург'),
            ('novosibirsk', 'Новосибирск'),
            ('kazan', 'Казань'),
            ('nizhny-novgorod', 'Нижний Новгород'),
            ('samara', 'Самара'),
            ('chelyabinsk', 'Челябинск'),
            ('rostov-on-don', 'Ростов-на-Дону'),
            ('ufa', 'Уфа'),
        ]
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['active_tab'] = self.request.GET.get('tab', 'overview')

        # Обновляем активность при просмотре профиля
        user.update_last_activity()

        if context['active_tab'] == 'overview':
            # Объявления пользователя (если есть приложение advertisements)
            try:
                from apps.advertisements.models import Ad
                context['user_ads'] = Ad.objects.filter(user=user).order_by('-created_at')[:3]
                context['user_ads_count'] = Ad.objects.filter(user=user).count()

                # Избранное
                context['user_favorites_count'] = Favorite.objects.filter(user=user).count()

                # Просмотры
                context['total_views'] = Ad.objects.filter(user=user).aggregate(
                    Sum('views')
                )['views__sum'] or 0

                # Непрочитанные сообщения
                context['unread_messages_count'] = Message.objects.filter(
                    recipient=user, is_read=False
                ).count()

            except ImportError:
                context['user_ads'] = []
                context['user_ads_count'] = 0
                context['user_favorites_count'] = 0
                context['total_views'] = 0
                context['unread_messages_count'] = 0

        elif context['active_tab'] == 'advertisements':
            # Статистика для фильтров
            try:
                from apps.advertisements.models import Ad
                context['all_ads_count'] = Ad.objects.filter(user=user).count()
                context['published_ads_count'] = Ad.objects.filter(user=user, status='published').count()
                context['draft_ads_count'] = Ad.objects.filter(user=user, status='draft').count()
                context['moderation_ads_count'] = Ad.objects.filter(user=user, status='moderation').count()
                context['rejected_ads_count'] = Ad.objects.filter(user=user, status='rejected').count()
            except ImportError:
                pass

        elif context['active_tab'] == 'messages':
            context['dialogs'] = self.get_dialogs()
            context['active_dialog'] = self.request.GET.get('dialog')

            if context['active_dialog']:
                context['dialog_user'] = get_object_or_404(User, id=context['active_dialog'])
                context['messages'] = Message.objects.filter(
                    Q(sender=user, recipient_id=context['active_dialog']) |
                    Q(sender_id=context['active_dialog'], recipient=user)
                ).order_by('created_at')

                # Помечаем сообщения как прочитанные
                Message.objects.filter(
                    recipient=user, sender_id=context['active_dialog'], is_read=False
                ).update(is_read=True)

        elif context['active_tab'] == 'settings':
            # Настройки пользователя
            context['user_settings'] = UserSettings.objects.get_or_create(user=user)[0]

        return context

    def get_dialogs(self):
        """Получение диалогов пользователя"""
        user = self.request.user
        messages = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('-created_at')

        dialogs = {}
        for msg in messages:
            other_user = msg.recipient if msg.sender == user else msg.sender
            if other_user.id not in dialogs:
                dialogs[other_user.id] = {
                    'user': other_user,
                    'last_message': msg.text[:100],
                    'last_time': msg.created_at,
                    'unread': msg.recipient == user and not msg.is_read
                }

        return list(dialogs.values())


class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = 'users/profile.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'edit'
        return context


class AccountSettingsView(LoginRequiredMixin, UpdateView):
    template_name = 'users/profile.html'
    fields = ['receive_email_notifications', 'receive_sms_notifications']
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Настройки сохранены!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'settings'
        return context


class EmailConfirmView(TemplateView):
    template_name = 'users/email_confirm.html'

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('uid')
        token = kwargs.get('token')

        try:
            user = User.objects.get(id=user_id)
            if user.verify_email(token):
                messages.success(request, 'Email успешно подтвержден!')
                context = {'success': True}
            else:
                messages.error(request, 'Ссылка для подтверждения недействительна или истекла.')
                context = {'success': False}
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден.')
            context = {'success': False}

        return self.render_to_response(context)


class MessagesView(LoginRequiredMixin, TemplateView):
    template_name = 'users/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Получаем диалоги
        messages = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('-created_at')

        dialogs = {}
        for msg in messages:
            other_user = msg.recipient if msg.sender == user else msg.sender
            if other_user.id not in dialogs:
                dialogs[other_user.id] = {
                    'user': other_user,
                    'last_message': msg.text[:100],
                    'last_time': msg.created_at,
                    'unread': msg.recipient == user and not msg.is_read
                }

        context['dialogs'] = list(dialogs.values())
        return context


class MessageDialogView(LoginRequiredMixin, TemplateView):
    template_name = 'users/message_dialog.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        other_user_id = kwargs.get('user_id')

        other_user = get_object_or_404(User, id=other_user_id)
        context['other_user'] = other_user

        # Получаем сообщения
        messages = Message.objects.filter(
            Q(sender=user, recipient=other_user) |
            Q(sender=other_user, recipient=user)
        ).order_by('created_at')

        # Помечаем сообщения как прочитанные
        unread_messages = messages.filter(recipient=user, is_read=False)
        for msg in unread_messages:
            msg.mark_as_read()

        context['messages'] = messages
        return context


@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(LoginRequiredMixin, FormView):
    """Отправка сообщения (для AJAX)"""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            recipient_id = data.get('recipient_id')
            message_text = data.get('message')
            ad_id = data.get('ad_id')

            if not recipient_id or not message_text:
                return JsonResponse({'success': False, 'error': 'Не указан получатель или текст сообщения'})

            recipient = get_object_or_404(User, id=recipient_id)

            # Создаем сообщение
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                text=message_text,
                is_read=False
            )

            # Если есть объявление
            if ad_id:
                try:
                    from apps.advertisements.models import Ad
                    ad = Ad.objects.get(id=ad_id)
                    message.ad = ad
                    message.save()
                except (ImportError, Ad.DoesNotExist):
                    pass

            # Создаем уведомление для получателя
            Notification.objects.create(
                user=recipient,
                notification_type='message',
                title=f'Новое сообщение от {request.user.username}',
                message=message_text[:100],
                is_read=False
            )

            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'created_at': message.created_at.strftime('%H:%M'),
                'sender_name': request.user.get_full_name() or request.user.username
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


# API функции для проверки
@require_http_methods(["GET"])
def check_username(request):
    """Проверка доступности имени пользователя"""
    username = request.GET.get('username', '')

    if not username:
        return JsonResponse({'available': False, 'message': 'Введите имя пользователя'})

    if len(username) < 3:
        return JsonResponse({'available': False, 'message': 'Имя должно быть не менее 3 символов'})

    if not username.replace('_', '').isalnum():
        return JsonResponse({'available': False, 'message': 'Только буквы, цифры и подчеркивания'})

    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': not exists})


@require_http_methods(["GET"])
def check_email(request):
    """Проверка доступности email"""
    email = request.GET.get('email', '')

    if not email:
        return JsonResponse({'available': False, 'message': 'Введите email'})

    if '@' not in email or '.' not in email:
        return JsonResponse({'available': False, 'message': 'Введите корректный email'})

    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'available': not exists})