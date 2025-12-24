# apps/users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

app_name = 'users'

urlpatterns = [
    # Регистрация и вход
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Профиль пользователя
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/settings/', views.AccountSettingsView.as_view(), name='settings'),

    # Восстановление пароля
    path('password/reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url='/users/password/reset/done/'
         ),
         name='password_reset'),

    path('password/reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('password/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/users/password/reset/complete/'
         ),
         name='password_reset_confirm'),

    path('password/reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Смена пароля
    path('password/change/',
         auth_views.PasswordChangeView.as_view(
             template_name='users/password_change.html',
             success_url='/users/password/change/done/'
         ),
         name='password_change'),

    path('password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ),
         name='password_change_done'),

    # Подтверждение email
    path('email/confirm/<int:uid>/<str:token>/',
         views.EmailConfirmView.as_view(),
         name='email_confirm'),

    path('email/confirm/sent/',
         TemplateView.as_view(template_name='users/email_confirm_sent.html'),
         name='email_confirm_sent'),

    # Сообщения
    path('messages/', views.MessagesView.as_view(), name='messages'),
    path('messages/<int:user_id>/', views.MessageDialogView.as_view(), name='messages_dialog'),
    path('messages/send/', views.SendMessageView.as_view(), name='send_message'),

    # API для проверки данных
    path('api/check-username/', views.check_username, name='check_username'),
    path('api/check-email/', views.check_email, name='check_email'),
]