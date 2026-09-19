import json
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.http import require_POST

from accounts.decorators import patient_required, doctor_required, admin_required
from accounts.models import User, DoctorProfile, PatientProfile
from health.models import HealthRecord, HealthAlert, SymptomAssessment
from appointments.models import Appointment, ConsultationRecord, Notification
from appointments.forms import ConsultationRecordForm
from health.gemini_service import generate_admin_summary


def home_view(request):
    """
    Public landing and welcome page.
    """
    if request.user.is_authenticated:
        if request.user.is_patient:
            return redirect('patient_dashboard')
        elif request.user.is_doctor:
            return redirect('doctor_dashboard')
        elif request.user.is_administrator:
            return redirect('admin_dashboard')

    featured_doctors = DoctorProfile.objects.filter(
        is_available=True,
        is_approved_by_admin=True
    ).select_related('user')[:8]

    stats = {
        'doctors_count': DoctorProfile.objects.filter(is_approved_by_admin=True).count(),
        'patients_count': User.objects.filter(role='patient').count(),
        'appointments_count': Appointment.objects.count(),
    }

    return render(request, 'home.html', {
        'featured_doctors': featured_doctors,
        'stats': stats,
    })


@patient_required
def patient_dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    # Latest vitals
    latest_record = HealthRecord.objects.filter(patient=user).first()

    # Active alerts
    active_alerts = HealthAlert.objects.filter(patient=user, is_resolved=False)[:3]

    # Upcoming appointment
    upcoming_appointment = Appointment.objects.filter(
        patient=user,
        appointment_date__gte=today,
        status__in=['pending', 'approved', 'in_progress']
    ).select_related('doctor__user').order_by('appointment_date', 'appointment_time').first()

    # Queue info if upcoming appointment exists
    queue_info = upcoming_appointment.get_queue_info() if upcoming_appointment else None

    # Latest AI Assessment
    latest_assessment = SymptomAssessment.objects.filter(patient=user).first()

    # Recommended doctors based on latest assessment or general
    if latest_assessment and latest_assessment.recommended_specialization:
        recommended_doctors = DoctorProfile.objects.filter(
            specialization=latest_assessment.recommended_specialization,
            is_available=True,
            is_approved_by_admin=True
        ).select_related('user')[:3]
        if not recommended_doctors.exists():
            recommended_doctors = DoctorProfile.objects.filter(
                is_available=True,
                is_approved_by_admin=True
            ).select_related('user')[:3]
    else:
        recommended_doctors = DoctorProfile.objects.filter(
            is_available=True,
            is_approved_by_admin=True
        ).select_related('user')[:3]

    # Recent 7 records for quick sparkline/trend
    recent_records = list(HealthRecord.objects.filter(patient=user).order_by('recorded_at')[:7])
    trend_labels = [r.recorded_at.strftime('%m/%d') for r in recent_records]
    trend_hr = [r.heart_rate for r in recent_records]
    trend_sys = [r.systolic_bp for r in recent_records]

    return render(request, 'patient/dashboard.html', {
        'latest_record': latest_record,
        'active_alerts': active_alerts,
        'upcoming_appointment': upcoming_appointment,
        'queue_info': queue_info,
        'latest_assessment': latest_assessment,
        'recommended_doctors': recommended_doctors,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_hr_json': json.dumps(trend_hr),
        'trend_sys_json': json.dumps(trend_sys),
    })


@doctor_required
@require_POST
def doctor_update_status_view(request):
    """Quick status toggle from the doctor dashboard (Available / Busy / Offline)."""
    doctor_profile = request.user.doctor_profile
    new_status = request.POST.get('status')
    if new_status in dict(DoctorProfile.STATUS_CHOICES):
        doctor_profile.current_status = new_status
        doctor_profile.save(update_fields=['current_status'])
        messages.success(request, f"Your status is now set to {doctor_profile.get_current_status_display()}.")
    return redirect('doctor_dashboard')


@doctor_required
def doctor_dashboard_view(request):
    doctor_profile = request.user.doctor_profile
    today = timezone.localdate()

    # Stats
    total_appointments = Appointment.objects.filter(doctor=doctor_profile).count()

    # Pending requests
    pending_requests = Appointment.objects.filter(
        doctor=doctor_profile,
        status='pending'
    ).select_related('patient', 'symptom_assessment').order_by('appointment_date', 'appointment_time')
    pending_requests_count = pending_requests.count()

    # Today's approved & active schedule
    today_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_date=today,
        status__in=['approved', 'in_progress', 'completed']
    ).select_related('patient', 'symptom_assessment').order_by('appointment_time')

    today_count = today_appointments.count()
    completed_count = Appointment.objects.filter(doctor=doctor_profile, status='completed').count()

    # Upcoming approved appointments (for future dates)
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_date__gt=today,
        status__in=['approved', 'in_progress']
    ).select_related('patient', 'symptom_assessment').order_by('appointment_date', 'appointment_time')[:6]

    # Patients with any appointment relationship (including a pending
    # request) under this doctor -- matches the access check used in
    # doctor_patient_detail_view, so "my patients" here always means the
    # doctor can actually open that patient's chart.
    patient_ids = set(Appointment.objects.filter(
        doctor=doctor_profile
    ).values_list('patient_id', flat=True).distinct())
    my_patients_count = len(patient_ids)

    # Platform-wide patient count (a number only -- no per-patient clinical
    # data is shown from this).
    total_registered_patients = User.objects.filter(role='patient').count()

    # Recent patients -- restricted to THIS doctor's own patients, since the
    # dashboard preview includes latest vitals and alert counts.
    recent_patients = list(
        User.objects.filter(role='patient', id__in=patient_ids)
        .prefetch_related('health_records', 'patient_profile', 'health_alerts')
        .order_by('-date_joined')[:8]
    )
    for p in recent_patients:
        p.is_my_patient = True
        p.latest_vital = p.health_records.first()
        p.active_alerts_count = p.health_alerts.filter(is_resolved=False).count()

    # Patient Health alerts -- restricted to this doctor's own patients only.
    patient_alerts = HealthAlert.objects.filter(
        patient_id__in=patient_ids,
        is_resolved=False
    ).select_related('patient').order_by('-created_at')[:5]

    return render(request, 'doctor/dashboard.html', {
        'doctor': doctor_profile,
        'total_appointments': total_appointments,
        'pending_requests': pending_requests,
        'pending_requests_count': pending_requests_count,
        'today_appointments': today_appointments,
        'today_count': today_count,
        'upcoming_appointments': upcoming_appointments,
        'upcoming_count': upcoming_appointments.count(),
        'completed_count': completed_count,
        'total_patients_count': my_patients_count,
        'total_registered_patients': total_registered_patients,
        'recent_patients': recent_patients,
        'patient_alerts': patient_alerts,
        'today': today,
    })


@doctor_required
def doctor_appointment_requests_view(request):
    doctor_profile = request.user.doctor_profile
    requests = Appointment.objects.filter(
        doctor=doctor_profile,
        status='pending'
    ).select_related('patient', 'symptom_assessment').order_by('appointment_date', 'appointment_time')

    return render(request, 'doctor/appointment_requests.html', {
        'requests': requests,
        'today': timezone.localdate(),
    })


@doctor_required
@require_POST
def doctor_appointment_action_view(request, appointment_id):
    doctor_profile = request.user.doctor_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor_profile)

    action = request.POST.get('action')
    reason = request.POST.get('rejection_reason', '').strip()
    schedule_today = request.POST.get('schedule_today')

    if action == 'accept':
        today = timezone.localdate()
        if schedule_today in ['true', '1', True]:
            appointment.appointment_date = today

        appointment.status = 'approved'
        appointment.save()

        # Notification for patient
        Notification.objects.create(
            user=appointment.patient,
            title="Appointment Confirmed & Scheduled!",
            message=f"Dr. {request.user.get_full_name_or_username()} has confirmed your appointment on {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}.",
            notification_type='appointment',
            link_url=f"/appointments/queue/{appointment.id}/"
        )

        # Notification for doctor
        Notification.objects.create(
            user=request.user,
            title="Appointment Confirmed",
            message=f"You confirmed appointment {appointment.appointment_id} for {appointment.patient.get_full_name_or_username()} on {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}.",
            notification_type='appointment',
            link_url=f"/doctor/appointments/today/?date={appointment.appointment_date}" if appointment.appointment_date != today else "/doctor/appointments/today/"
        )
        messages.success(request, f"Appointment {appointment.appointment_id} approved for {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}.")

    elif action == 'reschedule':
        new_date_str = request.POST.get('new_date', '').strip()
        new_time_str = request.POST.get('new_time', '').strip()
        reschedule_reason = request.POST.get('reschedule_reason', '').strip()

        if new_date_str:
            try:
                appointment.appointment_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if new_time_str:
            try:
                if len(new_time_str.split(':')) == 2:
                    appointment.appointment_time = datetime.strptime(new_time_str, '%H:%M').time()
                else:
                    appointment.appointment_time = datetime.strptime(new_time_str, '%H:%M:%S').time()
            except ValueError:
                pass

        appointment.status = 'approved'
        if reschedule_reason:
            appointment.notes = f"{appointment.notes or ''}\n[Rescheduled by Doctor]: {reschedule_reason}".strip()
        appointment.save()

        # Notification for patient
        Notification.objects.create(
            user=appointment.patient,
            title="Appointment Rescheduled & Approved",
            message=f"Dr. {request.user.get_full_name_or_username()} has rescheduled your appointment to {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}. Note: {reschedule_reason or 'Time adjusted by doctor.'}",
            notification_type='appointment',
            link_url=f"/appointments/queue/{appointment.id}/"
        )

        # Notification for doctor
        Notification.objects.create(
            user=request.user,
            title="Appointment Rescheduled",
            message=f"You rescheduled appointment {appointment.appointment_id} for {appointment.patient.get_full_name_or_username()} to {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}.",
            notification_type='appointment',
            link_url="/doctor/appointments/today/"
        )
        messages.success(request, f"Appointment {appointment.appointment_id} rescheduled and approved for {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}.")

    elif action == 'reject':
        appointment.status = 'rejected'
        appointment.rejection_reason = reason or "Doctor unavailable at requested time."
        appointment.save()

        # Notification for patient
        Notification.objects.create(
            user=appointment.patient,
            title="Appointment Request Declined",
            message=f"Your appointment request on {appointment.appointment_date.strftime('%b %d, %Y')} could not be accepted. Reason: {appointment.rejection_reason}",
            notification_type='appointment',
            link_url="/appointments/doctors/"
        )

        # Notification for doctor
        Notification.objects.create(
            user=request.user,
            title="Appointment Declined",
            message=f"You declined appointment {appointment.appointment_id} for {appointment.patient.get_full_name_or_username()}.",
            notification_type='appointment',
            link_url="/doctor/requests/"
        )
        messages.info(request, f"Appointment {appointment.appointment_id} rejected.")

    elif action == 'in_progress':
        appointment.status = 'in_progress'
        appointment.save()
        Notification.objects.create(
            user=appointment.patient,
            title="Your Turn: Consultation Started",
            message=f"Dr. {request.user.get_full_name_or_username()} is ready to begin your consultation. Please proceed to the consultation room.",
            notification_type='queue',
            link_url=f"/appointments/queue/{appointment.id}/"
        )
        messages.info(request, f"Consultation started for {appointment.patient.get_full_name_or_username()}.")

    elif action == 'cancel':
        appointment.status = 'cancelled'
        appointment.save()
        Notification.objects.create(
            user=appointment.patient,
            title="Appointment Cancelled",
            message=f"Your appointment on {appointment.appointment_date.strftime('%b %d, %Y')} was cancelled.",
            notification_type='appointment',
            link_url="/appointments/my-appointments/"
        )
        messages.info(request, "Appointment cancelled.")

    referer = request.META.get('HTTP_REFERER')
    if referer and 'action' not in referer:
        return redirect(referer)
    return redirect('doctor_dashboard')


@doctor_required
def doctor_today_appointments_view(request):
    doctor_profile = request.user.doctor_profile
    today = timezone.localdate()
    mode = request.GET.get('mode', 'today')  # 'today', 'upcoming', 'all'
    date_param = request.GET.get('date', '').strip()

    base_qs = Appointment.objects.filter(doctor=doctor_profile).select_related('patient', 'symptom_assessment')

    today_count = base_qs.filter(appointment_date=today, status__in=['approved', 'in_progress', 'completed']).count()
    upcoming_count = base_qs.filter(appointment_date__gt=today, status__in=['approved', 'in_progress']).count()
    all_count = base_qs.filter(status__in=['approved', 'in_progress', 'completed']).count()

    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            appointments = base_qs.filter(appointment_date=target_date, status__in=['approved', 'in_progress', 'completed']).order_by('appointment_time')
            title_text = f"Appointments for {target_date.strftime('%A, %B %d, %Y')}"
        except ValueError:
            appointments = base_qs.filter(appointment_date=today, status__in=['approved', 'in_progress', 'completed']).order_by('appointment_time')
            title_text = f"Today's Schedule ({today.strftime('%A, %B %d, %Y')})"
    elif mode == 'upcoming':
        appointments = base_qs.filter(appointment_date__gt=today, status__in=['approved', 'in_progress']).order_by('appointment_date', 'appointment_time')
        title_text = "Upcoming Approved Consultations"
    elif mode == 'all':
        appointments = base_qs.filter(status__in=['approved', 'in_progress', 'completed']).order_by('-appointment_date', 'appointment_time')
        title_text = "All Scheduled Consultations"
    else:  # mode == 'today'
        appointments = base_qs.filter(appointment_date=today, status__in=['approved', 'in_progress', 'completed']).order_by('appointment_time')
        title_text = f"Today's Clinic Schedule & Queue ({today.strftime('%A, %B %d, %Y')})"

    return render(request, 'doctor/today_appointments.html', {
        'appointments': appointments,
        'today': today,
        'mode': mode,
        'date_param': date_param,
        'today_count': today_count,
        'upcoming_count': upcoming_count,
        'all_count': all_count,
        'title_text': title_text,
    })


@doctor_required
def doctor_patient_list_view(request):
    doctor_profile = request.user.doctor_profile
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', 'all')  # Defaults to 'all' so every doctor sees all clinic patients

    # Patients who have any appointment (including a pending request) with
    # this doctor -- matches the access check in doctor_patient_detail_view,
    # so "My Patient" here always means the full chart is actually openable.
    my_patient_ids = set(Appointment.objects.filter(
        doctor=doctor_profile
    ).values_list('patient_id', flat=True).distinct())

    patients_qs = User.objects.filter(role='patient').prefetch_related(
        'health_records', 'appointments', 'patient_profile', 'health_alerts'
    ).order_by('first_name', 'last_name', 'username')

    if filter_type == 'my':
        patients_qs = patients_qs.filter(id__in=my_patient_ids)

    if query:
        patients_qs = patients_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(blood_group__iexact=query) |
            Q(patient_profile__medical_history__icontains=query) |
            Q(patient_profile__chronic_conditions__icontains=query)
        )

    patients = list(patients_qs)
    for p in patients:
        p.is_my_patient = p.id in my_patient_ids
        p.latest_vital = p.health_records.first()
        p.active_alerts_count = p.health_alerts.filter(is_resolved=False).count()

    return render(request, 'doctor/patient_list.html', {
        'patients': patients,
        'my_patient_ids': my_patient_ids,
        'filter_type': filter_type,
        'query': query,
        'total_registered_patients': User.objects.filter(role='patient').count(),
        'my_patients_count': len(my_patient_ids),
    })


@doctor_required
def doctor_patient_detail_view(request, patient_id):
    doctor_profile = request.user.doctor_profile
    patient = get_object_or_404(User, id=patient_id, role='patient')

    # A doctor may only open a patient's full clinical record if that patient
    # has actually booked (or requested) an appointment with THIS doctor at
    # some point -- pending requests count too, so the doctor can still
    # review full history before deciding to accept/reject. This enforces
    # the "prevent doctors from accessing unauthorized data" requirement
    # without blocking the doctor from reviewing a new request.
    has_appointment = Appointment.objects.filter(doctor=doctor_profile, patient=patient).exists()

    if not has_appointment:
        messages.error(
            request,
            f"Access restricted: {patient.get_full_name_or_username()} has no appointment history with you, "
            "so their full clinical record isn't available here."
        )
        return redirect('doctor_patient_list')

    health_records = HealthRecord.objects.filter(patient=patient).order_by('-recorded_at')
    health_alerts = HealthAlert.objects.filter(patient=patient).order_by('-created_at')
    consultations = ConsultationRecord.objects.filter(patient=patient).select_related('doctor__user').order_by('-visit_date')
    appointments = Appointment.objects.filter(patient=patient, doctor=doctor_profile).order_by('-appointment_date')

    # Chronological data for doctor patient health trends chart
    chrono_records = list(reversed(list(health_records[:20])))
    trend_labels = [r.recorded_at.strftime('%m/%d %H:%M') for r in chrono_records]
    trend_sys = [r.systolic_bp for r in chrono_records]
    trend_dia = [r.diastolic_bp for r in chrono_records]
    trend_hr = [r.heart_rate for r in chrono_records]
    trend_sugar = [float(r.blood_sugar) if r.blood_sugar else None for r in chrono_records]

    return render(request, 'doctor/patient_detail.html', {
        'patient': patient,
        'has_appointment': has_appointment,
        'health_records': health_records,
        'health_alerts': health_alerts,
        'consultations': consultations,
        'appointments': appointments,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_sys_json': json.dumps(trend_sys),
        'trend_dia_json': json.dumps(trend_dia),
        'trend_hr_json': json.dumps(trend_hr),
        'trend_sugar_json': json.dumps(trend_sugar),
    })


@doctor_required
def doctor_consultation_view(request, appointment_id):
    doctor_profile = request.user.doctor_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor_profile)

    # Check if consultation record already exists
    record = getattr(appointment, 'consultation_record', None)

    if request.method == 'POST':
        form = ConsultationRecordForm(request.POST, instance=record)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.appointment = appointment
            consultation.patient = appointment.patient
            consultation.doctor = doctor_profile
            consultation.save()

            # Mark appointment as completed
            appointment.status = 'completed'
            appointment.save()

            # Notify patient
            Notification.objects.create(
                user=appointment.patient,
                title="Prescription & Medical Notes Ready",
                message=f"Dr. {request.user.get_full_name_or_username()} has completed your consultation and issued medical notes/prescription.",
                notification_type='appointment',
                link_url=f"/appointments/medical-records/{consultation.id}/"
            )

            messages.success(request, f"Consultation finalized and prescription saved for {appointment.patient.get_full_name_or_username()}.")
            return redirect('prescription_detail', record_id=consultation.id)
        else:
            messages.error(request, "Please check consultation inputs.")
    else:
        # Prepopulate diagnosis or symptoms if available
        initial = {}
        if appointment.symptom_assessment:
            initial['symptoms_observed'] = appointment.symptom_assessment.symptoms
        form = ConsultationRecordForm(instance=record, initial=initial)

    # Patient latest vitals for reference
    latest_vitals = HealthRecord.objects.filter(patient=appointment.patient).first()

    return render(request, 'doctor/consultation_form.html', {
        'appointment': appointment,
        'form': form,
        'latest_vitals': latest_vitals,
    })


@admin_required
def admin_dashboard_view(request):
    total_patients = User.objects.filter(role='patient').count()
    total_doctors = DoctorProfile.objects.count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    active_alerts_count = HealthAlert.objects.filter(is_resolved=False).count()

    # Appointment status distribution for chart
    status_counts = dict(Appointment.objects.values_list('status').annotate(c=Count('id')))
    status_labels = ['Pending', 'Approved', 'In Progress', 'Completed', 'Cancelled', 'Rejected']
    status_values = [
        status_counts.get('pending', 0),
        status_counts.get('approved', 0),
        status_counts.get('in_progress', 0),
        status_counts.get('completed', 0),
        status_counts.get('cancelled', 0),
        status_counts.get('rejected', 0),
    ]

    # Specialization distribution
    spec_data = list(DoctorProfile.objects.values('specialization').annotate(total=Count('id')).order_by('-total')[:6])
    spec_labels = [s['specialization'] for s in spec_data]
    spec_values = [s['total'] for s in spec_data]

    recent_appointments = Appointment.objects.select_related('patient', 'doctor__user').order_by('-created_at')[:8]
    pending_doctors = DoctorProfile.objects.filter(is_approved_by_admin=False).select_related('user')

    return render(request, 'admin_portal/dashboard.html', {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,
        'active_alerts_count': active_alerts_count,
        'status_labels_json': json.dumps(status_labels),
        'status_values_json': json.dumps(status_values),
        'spec_labels_json': json.dumps(spec_labels),
        'spec_values_json': json.dumps(spec_values),
        'recent_appointments': recent_appointments,
        'pending_doctors': pending_doctors,
        'ai_summary': generate_admin_summary(
            total_patients, total_doctors, total_appointments,
            pending_appointments, completed_appointments, active_alerts_count
        )['summary'],
    })


@admin_required
def admin_patient_management_view(request):
    query = request.GET.get('q', '')
    patients = User.objects.filter(role='patient').prefetch_related('health_records', 'appointments')
    if query:
        patients = patients.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    return render(request, 'admin_portal/patient_management.html', {'patients': patients, 'query': query})


@admin_required
def admin_doctor_management_view(request):
    query = request.GET.get('q', '')
    doctors = DoctorProfile.objects.select_related('user').all()
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query) |
            Q(hospital_or_clinic__icontains=query)
        )
    return render(request, 'admin_portal/doctor_management.html', {'doctors': doctors, 'query': query})


@admin_required
@require_POST
def admin_toggle_doctor_approval(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor.is_approved_by_admin = not doctor.is_approved_by_admin
    doctor.save()
    status_str = "approved" if doctor.is_approved_by_admin else "unapproved"
    messages.success(request, f"Dr. {doctor.user.get_full_name_or_username()} is now {status_str}.")
    return redirect('admin_doctor_management')


@admin_required
@require_POST
def admin_toggle_patient_active(request, patient_id):
    """
    Activates or deactivates a patient's account. A deactivated account
    cannot log in (Django's auth backends check User.is_active), but all
    of the patient's existing data (records, appointments) is preserved.
    """
    patient = get_object_or_404(User, id=patient_id, role='patient')
    patient.is_active = not patient.is_active
    patient.save()
    status_str = "activated" if patient.is_active else "deactivated"
    messages.success(request, f"Patient account for {patient.get_full_name_or_username()} is now {status_str}.")
    return redirect('admin_patient_management')


@admin_required
@require_POST
def admin_toggle_doctor_active(request, doctor_id):
    """
    Activates or deactivates a doctor's login account (separate from
    admin approval/accreditation status). A deactivated doctor cannot
    log in until reactivated.
    """
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor.user.is_active = not doctor.user.is_active
    doctor.user.save()
    status_str = "activated" if doctor.user.is_active else "deactivated"
    messages.success(request, f"Dr. {doctor.user.get_full_name_or_username()}'s account is now {status_str}.")
    return redirect('admin_doctor_management')


@admin_required
def admin_appointment_management_view(request):
    status_filter = request.GET.get('status', 'all')
    appointments = Appointment.objects.select_related('patient', 'doctor__user').all().order_by('-appointment_date', '-appointment_time')

    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)

    return render(request, 'admin_portal/appointment_management.html', {
        'appointments': appointments,
        'status_filter': status_filter,
    })


@admin_required
def admin_reports_view(request):
    total_records = HealthRecord.objects.count()
    total_assessments = SymptomAssessment.objects.count()
    total_alerts = HealthAlert.objects.count()
    total_consultations = ConsultationRecord.objects.count()

    urgency_distribution = list(
        SymptomAssessment.objects.values('urgency_level').annotate(count=Count('id'))
    )

    return render(request, 'admin_portal/reports.html', {
        'total_records': total_records,
        'total_assessments': total_assessments,
        'total_alerts': total_alerts,
        'total_consultations': total_consultations,
        'urgency_distribution': urgency_distribution,
    })


@admin_required
def admin_health_record_management_view(request):
    """
    Supervises system-wide health vitals and telemetry records.
    """
    query = request.GET.get('q', '')
    records = HealthRecord.objects.select_related('patient').order_by('-recorded_at')

    if query:
        records = records.filter(
            Q(patient__username__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(notes__icontains=query)
        )

    return render(request, 'admin_portal/health_record_management.html', {
        'records': records,
        'query': query,
        'total_count': records.count(),
    })
