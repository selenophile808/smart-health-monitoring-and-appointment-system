from django.urls import path
from django.views.generic import RedirectView
from accounts.views import dashboard_redirect
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', dashboard_redirect, name='dashboard'),

    # Patient Dashboard
    path('patient/', RedirectView.as_view(pattern_name='patient_dashboard', permanent=False)),
    path('patient/dashboard/', views.patient_dashboard_view, name='patient_dashboard'),

    # Doctor Dashboard & Workflows
    path('doctor/', RedirectView.as_view(pattern_name='doctor_dashboard', permanent=False)),
    path('doctor/dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('doctor/status/', views.doctor_update_status_view, name='doctor_update_status'),
    path('doctor/requests/', views.doctor_appointment_requests_view, name='doctor_appointment_requests'),
    path('doctor/appointments/<int:appointment_id>/action/', views.doctor_appointment_action_view, name='doctor_appointment_action'),
    path('doctor/appointments/today/', views.doctor_today_appointments_view, name='doctor_today_appointments'),
    path('doctor/patients/', views.doctor_patient_list_view, name='doctor_patient_list'),
    path('doctor/patients/<int:patient_id>/', views.doctor_patient_detail_view, name='doctor_patient_detail'),
    path('doctor/consultation/<int:appointment_id>/', views.doctor_consultation_view, name='doctor_consultation'),

    # Admin Dashboard & Workflows
    path('admin/', RedirectView.as_view(pattern_name='admin_dashboard', permanent=False)),
    path('admin/dashboard/', RedirectView.as_view(pattern_name='admin_dashboard', permanent=False)),
    path('admin-portal/', RedirectView.as_view(pattern_name='admin_dashboard', permanent=False)),
    path('admin-portal/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-portal/patients/', views.admin_patient_management_view, name='admin_patient_management'),
    path('admin-portal/doctors/', views.admin_doctor_management_view, name='admin_doctor_management'),
    path('admin-portal/doctors/<int:doctor_id>/toggle-approval/', views.admin_toggle_doctor_approval, name='admin_toggle_doctor_approval'),
    path('admin-portal/doctors/<int:doctor_id>/toggle-active/', views.admin_toggle_doctor_active, name='admin_toggle_doctor_active'),
    path('admin-portal/patients/<int:patient_id>/toggle-active/', views.admin_toggle_patient_active, name='admin_toggle_patient_active'),
    path('admin-portal/appointments/', views.admin_appointment_management_view, name='admin_appointment_management'),
    path('admin-portal/health-records/', views.admin_health_record_management_view, name='admin_health_record_management'),
    path('admin-portal/reports/', views.admin_reports_view, name='admin_reports'),
]
