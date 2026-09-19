from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('patient/login/', views.login_view, name='patient_login'),
    path('doctor/login/', views.doctor_login_view, name='doctor_login'),
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.patient_register_view, name='patient_register'),
    path('doctor/register/', views.doctor_register_view, name='doctor_register'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
]

