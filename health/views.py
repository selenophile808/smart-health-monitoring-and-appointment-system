import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg, Max, Min

from accounts.decorators import patient_required
from accounts.models import DoctorProfile
from .models import HealthRecord, HealthAlert, SymptomAssessment, EmergencyAlert
from .forms import HealthRecordForm, SymptomAssessmentForm
from .gemini_service import assess_symptoms_with_gemini, chat_with_assistant, generate_trend_insight, explain_prescription, calculate_health_risk_score


@patient_required
def health_entry_view(request):
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = request.user
            record.save()
            alerts = record.check_and_create_alerts()

            if alerts:
                messages.warning(
                    request,
                    f"Vitals logged successfully. Note: {len(alerts)} automated health alert(s) were generated based on your readings."
                )
            else:
                messages.success(request, "Your health vitals have been recorded successfully.")
            return redirect('health_history')
        else:
            messages.error(request, "Please review the entered health metrics.")
    else:
        form = HealthRecordForm()

    return render(request, 'patient/health_entry.html', {'form': form})


@patient_required
def health_history_view(request):
    records = HealthRecord.objects.filter(patient=request.user)
    return render(request, 'patient/health_history.html', {'records': records})


@patient_required
def health_trends_view(request):
    days = int(request.GET.get('days', 30))
    if days not in [7, 30, 90]:
        days = 30

    start_date = timezone.now() - timedelta(days=days)
    records = list(HealthRecord.objects.filter(
        patient=request.user,
        recorded_at__gte=start_date
    ).order_by('recorded_at'))

    # Calculate statistics
    avg_hr = None
    avg_sys = None
    avg_dia = None
    avg_sugar = None
    latest_weight = None

    if records:
        hr_list = [r.heart_rate for r in records if r.heart_rate]
        sys_list = [r.systolic_bp for r in records if r.systolic_bp]
        dia_list = [r.diastolic_bp for r in records if r.diastolic_bp]
        sugar_list = [float(r.blood_sugar) for r in records if r.blood_sugar]
        weights = [float(r.weight) for r in records if r.weight]

        avg_hr = round(sum(hr_list) / len(hr_list), 1) if hr_list else None
        avg_sys = round(sum(sys_list) / len(sys_list), 1) if sys_list else None
        avg_dia = round(sum(dia_list) / len(dia_list), 1) if dia_list else None
        avg_sugar = round(sum(sugar_list) / len(sugar_list), 1) if sugar_list else None
        latest_weight = weights[-1] if weights else None

    # Chart datasets
    labels = [r.recorded_at.strftime('%b %d, %H:%M') for r in records]
    heart_rates = [r.heart_rate for r in records]
    systolic_bps = [r.systolic_bp for r in records]
    diastolic_bps = [r.diastolic_bp for r in records]
    blood_sugars = [float(r.blood_sugar) if r.blood_sugar else None for r in records]
    weights = [float(r.weight) if r.weight else None for r in records]
    oxygen_levels = [r.oxygen_saturation for r in records]

    chart_data = {
        'labels': labels,
        'heart_rates': heart_rates,
        'systolic_bps': systolic_bps,
        'diastolic_bps': diastolic_bps,
        'blood_sugars': blood_sugars,
        'weights': weights,
        'oxygen_levels': oxygen_levels,
    }

    return render(request, 'patient/health_trends.html', {
        'days': days,
        'records_count': len(records),
        'avg_hr': avg_hr,
        'avg_sys': avg_sys,
        'avg_dia': avg_dia,
        'avg_sugar': avg_sugar,
        'latest_weight': latest_weight,
        'chart_data_json': json.dumps(chart_data),
        'trend_insight': generate_trend_insight(len(records), avg_hr, avg_sys, avg_dia, avg_sugar, latest_weight, days=days)['insight'],
    })


@patient_required
def health_alerts_view(request):
    alerts = HealthAlert.objects.filter(patient=request.user)
    unresolved_count = alerts.filter(is_resolved=False).count()
    return render(request, 'patient/health_alerts.html', {
        'alerts': alerts,
        'unresolved_count': unresolved_count,
    })


@patient_required
def resolve_alert_view(request, alert_id):
    alert = get_object_or_404(HealthAlert, id=alert_id, patient=request.user)
    alert.resolve()
    messages.success(request, f"Alert '{alert.title}' marked as resolved.")
    return redirect('health_alerts')


@patient_required
def symptom_assessment_view(request):
    common_symptoms = [
        # General
        'Fever', 'Chills', 'Fatigue / Weakness', 'Unexplained Weight Loss',
        # Respiratory
        'Persistent Cough', 'Shortness of Breath', 'Chest Tightness', 'Sore Throat', 'Runny Nose',
        # Cardiovascular
        'Chest Pain', 'Heart Palpitations', 'High Blood Pressure', 'Swollen Ankles',
        # Neurological
        'Headache / Migraine', 'Dizziness / Lightheadedness', 'Numbness or Tingling', 'Tremors',
        # Digestive
        'Abdominal Pain', 'Nausea / Vomiting', 'Diarrhea', 'Acid Reflux / Heartburn',
        # Musculoskeletal
        'Joint Pain / Stiffness', 'Back Pain', 'Muscle Aches', 'Knee Pain',
        # Dermatology
        'Skin Rash', 'Itching', 'Acne', 'Skin Lesions / Hives',
        # Endocrine / Metabolic
        'Frequent Urination', 'Excessive Thirst', 'Sugar Spikes',
        # Psychological
        'Anxiety / Panic', 'Depressed Mood', 'Insomnia / Sleep Disturbance',
        # ENT & Eye
        'Earache', 'Sinus Congestion', 'Red Eyes / Eye Strain', 'Vision Blur'
    ]

    if request.method == 'POST':
        form = SymptomAssessmentForm(request.POST)
        if form.is_valid():
            symptoms = form.cleaned_data['symptoms']
            duration = form.cleaned_data['duration']
            severity = form.cleaned_data['severity']
            additional_info = form.cleaned_data['additional_info']

            if not symptoms:
                messages.error(request, "Please select or enter at least one symptom.")
                return render(request, 'health/symptom_assessment.html', {
                    'form': form,
                    'common_symptoms': common_symptoms
                })

            # Process with Gemini / Clinical fallback
            ai_result = assess_symptoms_with_gemini(
                symptoms_text=symptoms,
                duration=duration,
                severity=severity,
                additional_info=additional_info
            )

            # Save assessment
            assessment = SymptomAssessment.objects.create(
                patient=request.user,
                symptoms=symptoms,
                duration=duration,
                severity=severity,
                additional_info=additional_info,
                ai_response_raw=ai_result.get('raw_response', ''),
                possible_concerns=ai_result.get('possible_concerns', ''),
                recommended_specialization=ai_result.get('recommended_specialization', 'General Medicine'),
                urgency_level=ai_result.get('urgency_level', 'routine'),
                guidance_notes=ai_result.get('guidance_notes', '')
            )

            # Create notification
            from appointments.models import Notification
            Notification.objects.create(
                user=request.user,
                title="AI Symptom Assessment Completed",
                message=f"Your triage assessment is ready. Recommended specialization: {assessment.recommended_specialization}.",
                notification_type='appointment',
                link_url=f"/health/assessment/{assessment.id}/"
            )

            messages.success(request, f"Assessment completed via {ai_result.get('source', 'AI Engine')}.")
            return redirect('assessment_result', assessment_id=assessment.id)
        else:
            messages.error(request, "Please check your inputs.")
    else:
        form = SymptomAssessmentForm()

    return render(request, 'health/symptom_assessment.html', {
        'form': form,
        'common_symptoms': common_symptoms
    })


@patient_required
def assessment_result_view(request, assessment_id):
    assessment = get_object_or_404(SymptomAssessment, id=assessment_id, patient=request.user)

    # Find matching doctors
    doctors = DoctorProfile.objects.filter(
        specialization=assessment.recommended_specialization,
        is_available=True,
        is_approved_by_admin=True
    ).select_related('user')

    # Fallback to general physicians if no exact specialist found
    if not doctors.exists():
        fallback_doctors = DoctorProfile.objects.filter(
            specialization='General Medicine',
            is_available=True,
            is_approved_by_admin=True
        ).select_related('user')
    else:
        fallback_doctors = []

    return render(request, 'health/assessment_result.html', {
        'assessment': assessment,
        'doctors': doctors,
        'fallback_doctors': fallback_doctors,
    })


@patient_required
def doctor_recommendations_view(request):
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

    # Get latest assessment for suggestion banner
    latest_assessment = SymptomAssessment.objects.filter(patient=request.user).first()

    specializations = DoctorProfile.SPECIALIZATION_CHOICES

    return render(request, 'health/doctor_recommendations.html', {
        'doctors': doctors,
        'selected_specialization': specialization,
        'query': query,
        'specializations': specializations,
        'latest_assessment': latest_assessment,
    })


@patient_required
def personal_health_summary_view(request):
    """
    Consolidated personal health summary report card for patients.
    Suitable for clinical consultation preparation, emergency card, and printing.
    """
    patient = request.user
    patient_profile = getattr(patient, 'patient_profile', None)

    latest_record = HealthRecord.objects.filter(patient=patient).first()
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_records = HealthRecord.objects.filter(patient=patient, recorded_at__gte=thirty_days_ago)

    aggregates = recent_records.aggregate(
        avg_hr=Avg('heart_rate'),
        avg_sys=Avg('systolic_bp'),
        avg_dia=Avg('diastolic_bp'),
        avg_sugar=Avg('blood_sugar'),
        avg_spo2=Avg('oxygen_saturation')
    )

    active_alerts = HealthAlert.objects.filter(patient=patient, is_resolved=False).order_by('-created_at')[:5]

    from appointments.models import ConsultationRecord, Appointment
    consultations = ConsultationRecord.objects.filter(patient=patient).select_related('doctor__user').order_by('-visit_date')[:5]
    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        status__in=['pending', 'approved', 'in_progress']
    ).select_related('doctor__user').order_by('appointment_date', 'appointment_time')[:3]

    return render(request, 'patient/health_summary.html', {
        'patient': patient,
        'patient_profile': patient_profile,
        'latest_record': latest_record,
        'stats': aggregates,
        'active_alerts': active_alerts,
        'consultations': consultations,
        'upcoming_appointments': upcoming_appointments,
        'today': timezone.now().date(),
    })


@login_required
def chatbot_api_view(request):
    """
    Site-wide AI Assistant chat widget endpoint. Works for any logged-in
    role (patient/doctor/admin). Accepts POST with a JSON body: {"message": "..."}
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = request.POST

    message = (data.get('message') or '').strip()
    if not message:
        return JsonResponse({'success': False, 'error': 'Empty message'}, status=400)
    if len(message) > 1000:
        message = message[:1000]

    role = getattr(request.user, 'role', 'patient')
    result = chat_with_assistant(message, role=role)
    return JsonResponse(result)


@patient_required
def trigger_sos_view(request):
    """
    Patient-triggered Emergency SOS. Creates an EmergencyAlert and notifies
    every doctor and admin immediately. This is a project/demo feature and
    is explicitly NOT a replacement for calling real emergency services.
    """
    if request.method != 'POST':
        return redirect('patient_dashboard')

    from accounts.models import User
    from appointments.models import Notification

    message = request.POST.get('message', '').strip()
    alert = EmergencyAlert.objects.create(patient=request.user, message=message)

    responder_ids = User.objects.filter(role__in=['doctor', 'admin']).values_list('id', flat=True)
    Notification.objects.bulk_create([
        Notification(
            user_id=uid,
            title="🚨 Emergency SOS Alert",
            message=f"{request.user.get_full_name_or_username()} triggered an emergency SOS alert.",
            notification_type='health_alert',
            link_url='/emergency-alerts/'
        ) for uid in responder_ids
    ])

    messages.success(request, "Emergency alert sent. A doctor or admin has been notified. If this is a real emergency, please also call your local emergency number immediately.")
    return redirect('patient_dashboard')


@login_required
def emergency_alerts_view(request):
    """Doctor/Admin view of all emergency alerts, active first."""
    if not (request.user.is_doctor or request.user.is_administrator):
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard_redirect')

    alerts = EmergencyAlert.objects.select_related('patient', 'resolved_by').all()
    return render(request, 'health/emergency_alerts.html', {'alerts': alerts})


@login_required
def resolve_sos_view(request, alert_id):
    if not (request.user.is_doctor or request.user.is_administrator):
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard_redirect')
    if request.method != 'POST':
        return redirect('emergency_alerts')

    alert = get_object_or_404(EmergencyAlert, id=alert_id)
    alert.status = 'resolved'
    alert.resolved_at = timezone.now()
    alert.resolved_by = request.user
    alert.save()
    messages.success(request, "Emergency alert marked as resolved.")
    return redirect('emergency_alerts')


@patient_required
def health_timeline_view(request):
    """
    A single chronological timeline combining: health/vital records,
    appointments, AI symptom assessments, and prescriptions/consultations.
    """
    from appointments.models import Appointment, ConsultationRecord

    patient = request.user
    events = []

    for r in HealthRecord.objects.filter(patient=patient):
        events.append({
            'type': 'vitals', 'icon': 'bi-heart-pulse', 'color': 'teal',
            'timestamp': r.recorded_at,
            'title': 'Health Data Recorded',
            'detail': f"HR {r.heart_rate or '--'} bpm, BP {r.systolic_bp or '--'}/{r.diastolic_bp or '--'} mmHg, Sugar {r.blood_sugar or '--'} mg/dL",
        })

    for a in SymptomAssessment.objects.filter(patient=patient):
        events.append({
            'type': 'ai_assessment', 'icon': 'bi-stars', 'color': 'primary',
            'timestamp': a.created_at,
            'title': 'AI Risk Analysis Completed',
            'detail': f"Recommended: {a.recommended_specialization} \u2022 Urgency: {a.get_urgency_level_display()}",
            'link': f"/health/assessment/{a.id}/",
        })

    for apt in Appointment.objects.filter(patient=patient).select_related('doctor__user'):
        events.append({
            'type': 'appointment', 'icon': 'bi-calendar-check', 'color': 'info',
            'timestamp': apt.created_at,
            'title': f"Appointment Booked with Dr. {apt.doctor.user.get_full_name_or_username()}",
            'detail': f"{apt.appointment_date} at {apt.appointment_time.strftime('%I:%M %p')} \u2022 Status: {apt.get_status_display()}",
        })

    for c in ConsultationRecord.objects.filter(patient=patient).select_related('doctor__user'):
        events.append({
            'type': 'consultation', 'icon': 'bi-clipboard2-pulse', 'color': 'success',
            'timestamp': c.created_at,
            'title': f"Consultation Completed with Dr. {c.doctor.user.get_full_name_or_username()}",
            'detail': c.diagnosis,
            'link': f"/appointments/medical-records/{c.id}/",
        })

    events.sort(key=lambda e: e['timestamp'], reverse=True)

    return render(request, 'patient/health_timeline.html', {'events': events})


@patient_required
def health_risk_score_view(request):
    """
    AI Health Risk Score -- computed from the patient's most recent logged
    vitals using transparent rule-based logic (see calculate_health_risk_score).
    Not a medical diagnosis; a clear disclaimer is always shown.
    """
    latest_record = HealthRecord.objects.filter(patient=request.user).order_by('-recorded_at').first()

    result = None
    if latest_record:
        result = calculate_health_risk_score(latest_record)

    return render(request, 'patient/health_risk_score.html', {
        'record': latest_record,
        'result': result,
    })
