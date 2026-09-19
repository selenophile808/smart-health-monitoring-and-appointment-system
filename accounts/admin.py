from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DoctorProfile


class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    can_delete = False
    verbose_name_plural = 'Patient Profile'


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    verbose_name_plural = 'Doctor Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Profile Information', {
            'fields': ('role', 'phone_number', 'date_of_birth', 'gender', 'blood_group', 'address', 'profile_picture')
        }),
    )
    inlines = [PatientProfileInline, DoctorProfileInline]


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'emergency_contact_name', 'emergency_contact_phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'emergency_contact_name')


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 'is_available', 'is_approved_by_admin')
    list_filter = ('specialization', 'is_available', 'is_approved_by_admin')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization', 'hospital_or_clinic')
