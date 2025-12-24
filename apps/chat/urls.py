# apps/chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatListView.as_view(), name='chat_list'),
    path('<int:user_id>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('thread/<int:thread_id>/', views.ChatThreadView.as_view(), name='chat_thread'),
    path('create/', views.CreateChatView.as_view(), name='create_chat'),
    path('with-user/<int:user_id>/', views.ChatWithUserView.as_view(), name='chat_with_user'),
    path('message/send/', views.SendMessageView.as_view(), name='send_message'),
    path('message/<int:message_id>/delete/', views.DeleteMessageView.as_view(), name='delete_message'),

    # WebSocket/API
    path('api/messages/<int:thread_id>/', views.ChatMessagesAPIView.as_view(), name='api_messages'),
    path('api/unread-count/', views.UnreadMessagesCountAPIView.as_view(), name='api_unread_count'),
]