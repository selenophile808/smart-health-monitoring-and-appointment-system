from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.decorators import patient_required, doctor_required
from accounts.models import DoctorProfile, User
from health.models import SymptomAssessment
from .models import Appointment, ConsultationRecord, Notification, Review
from .forms import AppointmentBookingForm, ReviewForm
from health.gemini_service import explain_prescription


def doctor_list_view(request):
    specialization = request.GET.get('specialization', '')
    query = request.GET.get('q', '')

    doctors = DoctorProfile.objects.filter(
        is_available=True,
        is_approved_by_admin=True
    ).select_related('user')

    if specialization:
        doctors = doctors.filter(specialization=specialization)
    if query:
        doctors = doctors.filter(
            user__first_name__icontains=query
        ) | doctors.filter(
            user__last_name__icontains=query
        ) | doctors.filter(
            hospital_or_clinic__icontains=query
        )

    return render(request, 'appointments/doctor_list.html', {
        'doctors': doctors,
        'specializations': DoctorProfile.SPECIALIZATION_CHOICES,
        'selected_specialization': specialization,
        'query': query,
    })


def doctor_profile_view(request, doctor_id):
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related('user'),
        id=doctor_id,
        is_approved_by_admin=True
    )
    return render(request, 'appointments/doctor_profile.html', {'doctor': doctor})


@patient_required
def book_appointment_view(request):
    initial_data = {
        'appointment_date': timezone.localdate()
    }
    doctor_id = request.GET.get('doctor_id')
    assessment_id = request.GET.get('assessment_id')

    selected_doctor = None
    if doctor_id:
        selected_doctor = get_object_or_404(DoctorProfile, id=doctor_id, is_available=True, is_approved_by_admin=True)
        initial_data['doctor'] = selected_doctor

    assessment = None
    if assessment_id:
        assessment = SymptomAssessment.objects.filter(id=assessment_id, patient=request.user).first()
        if assessment:
            initial_data['reason_for_visit'] = f"Consultation for: {assessment.symptoms[:100]}"

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'pending'
            if assessment:
                appointment.symptom_assessment = assessment
            appointment.save()

            # Notify doctor
            Notification.objects.create(
                user=appointment.doctor.user,
                title="New Appointment Request",
                message=f"Patient {request.user.get_full_name_or_username()} requested an appointment on {appointment.appointment_date.strftime('%b %d, %Y')} at {appointment.appointment_time.strftime('%I:%M %p')}.",
                notification_type='appointment',
                link_url='/doctor/requests/'
            )

            # Notify patient
            Notification.objects.create(
                user=request.user,
                title="Appointment Booking Submitted",
                message=f"Your appointment request with Dr. {appointment.doctor.user.get_full_name_or_username()} has been received (ID: {appointment.appointment_id}).",
                notification_type='appointment',
                link_url=f"/appointments/queue/{appointment.id}/"
            )

            messages.success(request, f"Appointment booked successfully! Appointment ID: {appointment.appointment_id}")
            return redirect('appointment_confirmation', appointment_id=appointment.appointment_id)
        else:
            messages.error(request, "Unable to book appointment. Please check the highlighted errors.")
    else:
        form = AppointmentBookingForm(initial=initial_data)

    return render(request, 'appointments/book_appointment.html', {
        'form': form,
        'selected_doctor': selected_doctor,
        'assessment': assessment,
    })


def get_available_slots_api(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Missing doctor_id or date parameter'}, status=400)

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (DoctorProfile.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid doctor or date'}, status=400)

    # Check if doctor is available on this day
    day_name = target_date.strftime('%A')
    available_days = doctor.get_available_days_list()
    if available_days and day_name not in available_days:
        return JsonResponse({
            'available': False,
            'message': f"Doctor is not available on {day_name}s.",
            'slots': []
        })

    # Generate time slots
    slot_minutes = doctor.slot_duration_minutes or 30
    start_time = doctor.start_time
    end_time = doctor.end_time

    # Find booked slots
    booked_times = list(Appointment.objects.filter(
        doctor=doctor,
        appointment_date=target_date,
        status__in=['pending', 'approved', 'in_progress']
    ).values_list('appointment_time', flat=True))
    booked_time_strings = [t.strftime('%H:%M') for t in booked_times]

    slots = []
    current_dt = datetime.combine(target_date, start_time)
    end_dt = datetime.combine(target_date, end_time)

    # Check if target_date is today and skip past times
    now = timezone.localtime(timezone.now())
    is_today = (target_date == now.date())

    while current_dt + timedelta(minutes=slot_minutes) <= end_dt:
        time_str = current_dt.strftime('%H:%M')
        display_str = current_dt.strftime('%I:%M %p')

        is_past = False
        if is_today and current_dt.time() <= now.time():
            is_past = True

        is_booked = time_str in booked_time_strings

        slots.append({
            'time': time_str,
            'display': display_str,
            'is_available': (not is_booked) and (not is_past),
            'status': 'Booked' if is_booked else ('Past' if is_past else 'Available')
        })
        current_dt += timedelta(minutes=slot_minutes)

    return JsonResponse({
        'available': True,
        'slots': slots,
        'doctor_name': doctor.user.get_full_name_or_username(),
        'slot_duration': slot_minutes
    })


@login_required
def appointment_confirmation_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    # Check permissions
    if not (request.user == appointment.patient or request.user == appointment.doctor.user or request.user.is_administrator):
        messages.error(request, "Unauthorized access to this appointment confirmation.")
        return redirect('dashboard_redirect')

    queue_info = appointment.get_queue_info()
    return render(request, 'appointments/appointment_confirmation.html', {
        'appointment': appointment,
        'queue_info': queue_info,
    })


@patient_required
def my_appointments_view(request):
    status_filter = request.GET.get('status', 'all')
    appointments = Appointment.objects.filter(patient=request.user).select_related('doctor__user')

    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)

    return render(request, 'patient/my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
    })


@patient_required
@require_POST
def cancel_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if appointment.status in ['pending', 'approved']:
        appointment.status = 'cancelled'
        appointment.save()

        # Notify doctor
        Notification.objects.create(
            user=appointment.doctor.user,
            title="Appointment Cancelled by Patient",
            message=f"Appointment with {request.user.get_full_name_or_username()} on {appointment.appointment_date} at {appointment.appointment_time.strftime('%H:%M')} has been cancelled.",
            notification_type='appointment',
            link_url='/doctor/appointments/today/'
        )

        messages.info(request, "Your appointment has been cancelled.")
    else:
        messages.error(request, "This appointment cannot be cancelled in its current state.")

    return redirect('my_appointments')


@login_required
def queue_status_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Permission check: patient or doctor or admin
    if not (request.user == appointment.patient or request.user == appointment.doctor.user or request.user.is_administrator):
        messages.error(request, "Access restricted.")
        return redirect('dashboard_redirect')

    queue_info = appointment.get_queue_info()

    # Get appointments ahead details if available
    preceding_count = queue_info.get('patients_ahead', 0)

    return render(request, 'patient/queue_status.html', {
        'appointment': appointment,
        'queue_info': queue_info,
        'preceding_count': preceding_count,
    })


@login_required
def queue_status_api(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if not (request.user == appointment.patient or request.user == appointment.doctor.user or request.user.is_administrator):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    queue_info = appointment.get_queue_info()
    return JsonResponse({
        'status': 'success',
        'appointment_id': appointment.appointment_id,
        'queue_position': queue_info.get('queue_position'),
        'patients_ahead': queue_info.get('patients_ahead'),
        'estimated_wait_time_minutes': queue_info.get('estimated_wait_time_minutes'),
        'current_status': queue_info.get('current_status'),
        'last_updated': timezone.now().strftime('%H:%M:%S'),
    })


@patient_required
def medical_records_view(request):
    records = ConsultationRecord.objects.filter(
        patient=request.user
    ).select_related('doctor__user', 'appointment').order_by('-visit_date')
    return render(request, 'patient/medical_records.html', {'records': records})


@login_required
def prescription_detail_view(request, record_id):
    record = get_object_or_404(
        ConsultationRecord.objects.select_related('patient', 'doctor__user', 'appointment'),
        id=record_id
    )
    # Check permissions
    if not (request.user == record.patient or request.user == record.doctor.user or request.user.is_administrator):
        messages.error(request, "Unauthorized access to medical record.")
        return redirect('dashboard_redirect')

    # Parse prescription items into structured rows
    prescription_lines = [line.strip() for line in record.prescription_items.split('\n') if line.strip()]

    return render(request, 'patient/prescription_detail.html', {
        'record': record,
        'prescription_lines': prescription_lines,
    })


@login_required
def explain_prescription_api_view(request, record_id):
    """
    AJAX endpoint: returns a plain-language explanation of a consultation's
    diagnosis + prescription for the "Explain in simple terms" button.
    """
    record = get_object_or_404(ConsultationRecord.objects.select_related('patient', 'doctor__user'), id=record_id)
    if not (request.user == record.patient or request.user == record.doctor.user or request.user.is_administrator):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    result = explain_prescription(record.diagnosis, record.prescription_items, record.clinical_notes)
    return JsonResponse(result)


@patient_required
def submit_review_view(request, appointment_id):
    """
    Lets a patient rate/review a doctor after a completed appointment.
    Only the patient who completed that specific appointment may review it,
    and only once (OneToOneField on Review.appointment enforces "once").
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if appointment.status != 'completed':
        messages.error(request, "You can only review a doctor after your appointment is completed.")
        return redirect('my_appointments')

    existing = Review.objects.filter(appointment=appointment).first()
    if existing:
        messages.info(request, "You've already reviewed this appointment.")
        return redirect('my_appointments')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.patient = request.user
            review.doctor = appointment.doctor
            review.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('my_appointments')
    else:
        form = ReviewForm()

    return render(request, 'patient/submit_review.html', {
        'form': form,
        'appointment': appointment,
    })
