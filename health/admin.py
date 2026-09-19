from django.contrib import admin
from .models import HealthRecord, HealthAlert, SymptomAssessment


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'recorded_at', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'blood_sugar', 'oxygen_saturation')
    list_filter = ('recorded_at',)
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name')


@admin.register(HealthAlert)
class HealthAlertAdmin(admin.ModelAdmin):
    list_display = ('patient', 'title', 'alert_type', 'severity', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_resolved')
    search_fields = ('patient__username', 'title', 'message')


@admin.register(SymptomAssessment)
class SymptomAssessmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'recommended_specialization', 'urgency_level', 'severity', 'created_at')
    list_filter = ('recommended_specialization', 'urgency_level', 'severity')
    search_fields = ('patient__username', 'symptoms', 'possible_concerns')
