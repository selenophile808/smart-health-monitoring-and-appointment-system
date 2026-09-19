from django.contrib import admin
from .models import Appointment, ConsultationRecord, Notification


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('appointment_id', 'patient__username', 'patient__first_name', 'doctor__user__username')


@admin.register(ConsultationRecord)
class ConsultationRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'visit_date', 'diagnosis', 'follow_up_date')
    search_fields = ('patient__username', 'doctor__user__username', 'diagnosis')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
