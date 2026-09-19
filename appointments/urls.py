from django.urls import path
from . import views

urlpatterns = [
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctors/<int:doctor_id>/', views.doctor_profile_view, name='doctor_profile'),
    path('book/', views.book_appointment_view, name='book_appointment'),
    path('slots-api/', views.get_available_slots_api, name='slots_api'),
    path('confirmation/<str:appointment_id>/', views.appointment_confirmation_view, name='appointment_confirmation'),
    path('my-appointments/', views.my_appointments_view, name='my_appointments'),
    path('<int:appointment_id>/cancel/', views.cancel_appointment_view, name='cancel_appointment'),
    path('queue/<int:appointment_id>/', views.queue_status_view, name='queue_status'),
    path('queue-api/<int:appointment_id>/', views.queue_status_api, name='queue_status_api'),
    path('medical-records/', views.medical_records_view, name='medical_records'),
    path('medical-records/<int:record_id>/', views.prescription_detail_view, name='prescription_detail'),
    path('medical-records/<int:record_id>/explain/', views.explain_prescription_api_view, name='explain_prescription_api'),
    path('review/<int:appointment_id>/', views.submit_review_view, name='submit_review'),
]
