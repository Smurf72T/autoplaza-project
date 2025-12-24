# apps/chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from .models import ChatThread, ChatMessage, ChatNotification
from apps.users.models import User
from apps.advertisements.models import CarAd


class ChatListView(LoginRequiredMixin, ListView):
    """Список чатов пользователя"""
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'
    paginate_by = 20

    def get_queryset(self):
        return ChatThread.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user),
            is_active=True
        ).select_related(
            'user1', 'user2', 'last_message'
        ).prefetch_related(
            'messages'
        ).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = ChatMessage.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        return context


class ChatDetailView(LoginRequiredMixin, DetailView):
    """Детали чата"""
    template_name = 'chat/chat_detail.html'
    model = ChatThread
    context_object_name = 'chat'

    def get_queryset(self):
        return ChatThread.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user),
            is_active=True
        ).select_related('user1', 'user2')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = self.object

        # Получаем сообщения
        messages = ChatMessage.objects.filter(
            thread=chat
        ).select_related('sender', 'recipient', 'car_ad').order_by('created_at')

        # Помечаем сообщения как прочитанные
        ChatMessage.objects.filter(
            thread=chat,
            recipient=self.request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        context['messages'] = messages
        context['other_user'] = chat.get_other_user(self.request.user)

        return context


class CreateChatView(LoginRequiredMixin, View):
    """Создание нового чата"""

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        ad_id = request.POST.get('ad_id')

        target_user = get_object_or_404(User, id=user_id)
        car_ad = get_object_or_404(CarAd, id=ad_id) if ad_id else None

        # Проверяем, существует ли уже чат
        chat = ChatThread.objects.filter(
            Q(user1=request.user, user2=target_user) |
            Q(user1=target_user, user2=request.user)
        ).first()

        if not chat:
            chat = ChatThread.objects.create(
                user1=request.user,
                user2=target_user
            )

        # Если есть объявление, создаем первое сообщение
        if car_ad:
            ChatMessage.objects.create(
                thread=chat,
                sender=request.user,
                recipient=target_user,
                text=f'Здравствуйте! Меня интересует ваше объявление "{car_ad.title}"',
                car_ad=car_ad
            )

        return redirect('chat:chat_detail', pk=chat.pk)


class SendMessageView(LoginRequiredMixin, View):
    """Отправка сообщения"""

    def post(self, request, *args, **kwargs):
        thread_id = request.POST.get('thread_id')
        message_text = request.POST.get('message')

        thread = get_object_or_404(ChatThread, id=thread_id)

        # Проверяем, что пользователь участник чата
        if request.user not in [thread.user1, thread.user2]:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        # Определяем получателя
        recipient = thread.user2 if request.user == thread.user1 else thread.user1

        # Создаем сообщение
        message = ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            recipient=recipient,
            text=message_text
        )

        # Обновляем последнее сообщение в чате
        thread.last_message = message
        thread.updated_at = timezone.now()
        thread.save()

        # Создаем уведомление
        ChatNotification.objects.create(
            user=recipient,
            message=message
        )

        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'created_at': message.created_at.isoformat()
        })


class GetMessagesView(LoginRequiredMixin, View):
    """Получение сообщений чата"""

    def get(self, request, *args, **kwargs):
        thread_id = request.GET.get('thread_id')
        last_message_id = request.GET.get('last_message_id', 0)

        thread = get_object_or_404(ChatThread, id=thread_id)

        # Проверяем доступ
        if request.user not in [thread.user1, thread.user2]:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        # Получаем новые сообщения
        messages = ChatMessage.objects.filter(
            thread=thread,
            id__gt=last_message_id
        ).select_related('sender', 'car_ad').order_by('created_at')

        # Помечаем как прочитанные
        unread_messages = messages.filter(
            recipient=request.user,
            is_read=False
        )
        unread_messages.update(is_read=True, read_at=timezone.now())

        # Формируем ответ
        data = {
            'messages': [
                {
                    'id': msg.id,
                    'sender_id': msg.sender.id,
                    'sender_name': msg.sender.get_full_name() or msg.sender.username,
                    'sender_avatar': msg.sender.avatar.url if msg.sender.avatar else None,
                    'text': msg.text,
                    'created_at': msg.created_at.isoformat(),
                    'has_ad': bool(msg.car_ad),
                    'ad_title': msg.car_ad.title if msg.car_ad else None,
                    'ad_id': msg.car_ad.id if msg.car_ad else None,
                }
                for msg in messages
            ]
        }

        return JsonResponse(data)


class UnreadCountView(LoginRequiredMixin, View):
    """Количество непрочитанных сообщений"""

    def get(self, request, *args, **kwargs):
        count = ChatMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return JsonResponse({'count': count})

class ChatThreadView(LoginRequiredMixin, DetailView):
    """Просмотр чата по ID треда"""
    template_name = 'chat/chat_detail.html'
    model = ChatThread
    context_object_name = 'chat'

    def get_queryset(self):
        return ChatThread.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user),
            is_active=True
        ).select_related('user1', 'user2')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = self.object

        # Получаем сообщения
        messages = ChatMessage.objects.filter(
            thread=chat
        ).select_related('sender', 'recipient', 'car_ad').order_by('created_at')

        # Помечаем сообщения как прочитанные
        ChatMessage.objects.filter(
            thread=chat,
            recipient=self.request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        context['messages'] = messages
        context['other_user'] = chat.get_other_user(self.request.user)

        return context


class DeleteMessageView(LoginRequiredMixin, View):
    """Удаление сообщения"""

    def post(self, request, *args, **kwargs):
        message_id = kwargs.get('message_id')
        message = get_object_or_404(ChatMessage, id=message_id)

        # Проверяем, что пользователь - отправитель сообщения
        if message.sender != request.user:
            return JsonResponse({'error': 'Вы можете удалять только свои сообщения'}, status=403)

        # Помечаем как удаленное (мягкое удаление)
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()

        return JsonResponse({'success': True})


class ChatMessagesAPIView(LoginRequiredMixin, View):
    """API для получения сообщений (уже есть GetMessagesView)"""

    def get(self, request, *args, **kwargs):
        # Просто используем существующий класс
        return GetMessagesView.as_view()(request, *args, **kwargs)


class UnreadMessagesCountAPIView(LoginRequiredMixin, View):
    """API для количества непрочитанных сообщений (уже есть UnreadCountView)"""

    def get(self, request, *args, **kwargs):
        # Просто используем существующий класс
        return UnreadCountView.as_view()(request, *args, **kwargs)


class ChatWithUserView(LoginRequiredMixin, View):
    """Чат с конкретным пользователем"""

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        target_user = get_object_or_404(User, id=user_id)

        # Ищем существующий чат
        chat = ChatThread.objects.filter(
            Q(user1=request.user, user2=target_user) |
            Q(user1=target_user, user2=request.user)
        ).first()

        if chat:
            return redirect('chat:chat_detail', pk=chat.pk)

        # Создаем новый чат
        chat = ChatThread.objects.create(
            user1=request.user,
            user2=target_user
        )

        return redirect('chat:chat_detail', pk=chat.pk)