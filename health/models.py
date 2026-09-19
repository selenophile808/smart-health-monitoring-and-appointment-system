from django.db import models
from django.conf import settings
from django.utils import timezone


class HealthRecord(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_records'
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text="BPM (beats per min)")
    systolic_bp = models.PositiveIntegerField(null=True, blank=True, help_text="Systolic BP (mmHg)")
    diastolic_bp = models.PositiveIntegerField(null=True, blank=True, help_text="Diastolic BP (mmHg)")
    blood_sugar = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Blood Sugar (mg/dL)")
    weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Weight (kg)")
    height = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Height (cm)")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Temperature (°F)")
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True, help_text="SpO2 (%)")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-recorded_at']

    def calculate_bmi(self):
        if self.weight and self.height and self.height > 0:
            height_in_meters = float(self.height) / 100.0
            bmi = float(self.weight) / (height_in_meters ** 2)
            return round(bmi, 1)
        return None

    def get_bp_status(self):
        if not self.systolic_bp or not self.diastolic_bp:
            return None, 'secondary'
        sys, dia = self.systolic_bp, self.diastolic_bp
        if sys > 180 or dia > 120:
            return 'Hypertensive Crisis', 'danger'
        elif sys >= 140 or dia >= 90:
            return 'Stage 2 Hypertension', 'danger'
        elif sys >= 130 or dia >= 80:
            return 'Stage 1 Hypertension', 'warning'
        elif sys >= 120 and dia < 80:
            return 'Elevated BP', 'info'
        else:
            return 'Normal BP', 'success'

    def get_heart_rate_status(self):
        if not self.heart_rate:
            return None, 'secondary'
        hr = self.heart_rate
        if hr > 110:
            return 'Tachycardia (High)', 'danger'
        elif hr > 100:
            return 'Slightly Elevated', 'warning'
        elif hr < 50:
            return 'Bradycardia (Low)', 'danger'
        elif hr < 60:
            return 'Slightly Low', 'warning'
        else:
            return 'Normal Pulse', 'success'

    def get_blood_sugar_status(self):
        if not self.blood_sugar:
            return None, 'secondary'
        sugar = float(self.blood_sugar)
        if sugar >= 200:
            return 'High / Diabetic Alert', 'danger'
        elif sugar >= 140:
            return 'Elevated', 'warning'
        elif sugar < 70:
            return 'Hypoglycemia (Low)', 'danger'
        else:
            return 'Normal Sugar', 'success'

    def get_oxygen_status(self):
        if not self.oxygen_saturation:
            return None, 'secondary'
        spo2 = self.oxygen_saturation
        if spo2 < 90:
            return 'Severe Hypoxia', 'danger'
        elif spo2 < 95:
            return 'Low Oxygen', 'warning'
        else:
            return 'Normal Oxygen', 'success'

    def check_and_create_alerts(self):
        alerts = []
        # BP Alert
        if self.systolic_bp and self.diastolic_bp:
            if self.systolic_bp > 180 or self.diastolic_bp > 120:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='blood_pressure',
                    title='Critical Blood Pressure Alert',
                    message=f'Recorded Blood Pressure is dangerously high: {self.systolic_bp}/{self.diastolic_bp} mmHg. Please seek immediate medical evaluation.',
                    severity='critical'
                ))
            elif self.systolic_bp >= 140 or self.diastolic_bp >= 90:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='blood_pressure',
                    title='High Blood Pressure Notice',
                    message=f'Blood Pressure reading ({self.systolic_bp}/{self.diastolic_bp} mmHg) indicates Stage 2 Hypertension. Monitor regularly and consult your doctor.',
                    severity='high'
                ))

        # Heart Rate Alert
        if self.heart_rate:
            if self.heart_rate > 120:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='heart_rate',
                    title='Elevated Heart Rate Alert',
                    message=f'Heart rate recorded at {self.heart_rate} BPM (Tachycardia). Rest and consult a physician if accompanied by chest discomfort or dizziness.',
                    severity='high'
                ))
            elif self.heart_rate < 50:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='heart_rate',
                    title='Low Heart Rate Alert',
                    message=f'Heart rate recorded at {self.heart_rate} BPM (Bradycardia). Please report this to your doctor if you experience fatigue or fainting.',
                    severity='high'
                ))

        # Oxygen Alert
        if self.oxygen_saturation:
            if self.oxygen_saturation < 90:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='oxygen',
                    title='Critical Oxygen Saturation Alert',
                    message=f'SpO2 is low at {self.oxygen_saturation}%. Inadequate oxygenation requires immediate medical attention.',
                    severity='critical'
                ))
            elif self.oxygen_saturation < 95:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='oxygen',
                    title='Low Blood Oxygen Warning',
                    message=f'SpO2 reading of {self.oxygen_saturation}% is lower than normal healthy baseline (95-100%).',
                    severity='medium'
                ))

        # Blood Sugar Alert
        if self.blood_sugar:
            sugar = float(self.blood_sugar)
            if sugar >= 200:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='blood_sugar',
                    title='Elevated Blood Sugar Alert',
                    message=f'Blood sugar registered at {sugar} mg/dL. Consult your endocrinologist or primary care physician for diabetes management.',
                    severity='high'
                ))
            elif sugar < 70:
                alerts.append(HealthAlert(
                    patient=self.patient,
                    health_record=self,
                    alert_type='blood_sugar',
                    title='Hypoglycemia Warning',
                    message=f'Blood sugar is low at {sugar} mg/dL. Consume fast-acting carbohydrates and recheck soon.',
                    severity='high'
                ))

        if alerts:
            HealthAlert.objects.bulk_create(alerts)
            # Create a notification for the patient
            from appointments.models import Notification
            for alert in alerts:
                Notification.objects.create(
                    user=self.patient,
                    title=alert.title,
                    message=alert.message,
                    notification_type='health_alert',
                    link_url='/health/alerts/'
                )

            # Also notify attending/consulting doctors under whose care this patient is
            from accounts.models import User
            caring_doctors = User.objects.filter(
                doctor_profile__appointments__patient=self.patient,
                doctor_profile__appointments__status__in=['approved', 'in_progress', 'completed']
            ).distinct()

            for doc_user in caring_doctors:
                for alert in alerts:
                    Notification.objects.create(
                        user=doc_user,
                        title=f"Patient Health Alert: {self.patient.get_full_name_or_username()}",
                        message=f"{self.patient.get_full_name_or_username()}: {alert.title} - {alert.message}",
                        notification_type='health_alert',
                        link_url=f"/doctor/patients/{self.patient.id}/"
                    )
        return alerts

    def __str__(self):
        return f"Vitals for {self.patient.get_full_name_or_username()} on {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"


class HealthAlert(models.Model):
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    ALERT_TYPE_CHOICES = (
        ('blood_pressure', 'Blood Pressure'),
        ('heart_rate', 'Heart Rate'),
        ('blood_sugar', 'Blood Sugar'),
        ('oxygen', 'Oxygen SpO2'),
        ('temperature', 'Temperature'),
        ('general', 'General Health Alert'),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_alerts'
    )
    health_record = models.ForeignKey(
        HealthRecord,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='alerts'
    )
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES, default='general')
    title = models.CharField(max_length=150)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def resolve(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()

    def get_badge_class(self):
        mapping = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger',
        }
        return mapping.get(self.severity, 'secondary')

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title} - {self.patient.get_full_name_or_username()}"


class SymptomAssessment(models.Model):
    SEVERITY_CHOICES = (
        ('mild', 'Mild (Manageable with minimal disruption)'),
        ('moderate', 'Moderate (Noticeable disruption to daily activities)'),
        ('severe', 'Severe (Intense pain or significant impairment)'),
    )

    URGENCY_CHOICES = (
        ('routine', 'Routine Care (Schedule when convenient)'),
        ('consult_soon', 'Consult Soon (Within 1-2 days)'),
        ('urgent', 'Urgent Medical Attention (Same day recommended)'),
        ('emergency', 'Emergency Care (Immediate ER / Ambulance)'),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='symptom_assessments'
    )
    symptoms = models.TextField(help_text="Comma-separated symptoms or summary")
    duration = models.CharField(max_length=100)
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, default='mild')
    additional_info = models.TextField(blank=True, null=True)

    # AI Output
    ai_response_raw = models.TextField(blank=True, null=True)
    possible_concerns = models.TextField(help_text="General health concern categories identified")
    recommended_specialization = models.CharField(max_length=100, default='General Medicine')
    urgency_level = models.CharField(max_length=50, choices=URGENCY_CHOICES, default='routine')
    guidance_notes = models.TextField()
    disclaimer = models.TextField(
        default="NOTICE: This assessment is generated by an AI assistant for general informational and triage guidance only. It is not a clinical diagnosis or medical treatment plan. If you experience severe symptoms like chest pain, severe breathlessness, or stroke signs, call emergency services immediately."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def get_urgency_badge_class(self):
        mapping = {
            'routine': 'success',
            'consult_soon': 'info',
            'urgent': 'warning',
            'emergency': 'danger',
        }
        return mapping.get(self.urgency_level, 'secondary')

    def __str__(self):
        return f"Assessment for {self.patient.get_full_name_or_username()} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class EmergencyAlert(models.Model):
    """
    A patient-triggered SOS emergency alert. Immediately visible to doctors
    and admins so someone can respond. This is a project/demo feature and is
    NOT a replacement for calling real emergency services.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('resolved', 'Resolved'),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_alerts'
    )
    message = models.TextField(blank=True, null=True, help_text="Optional note from the patient about what's wrong")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_alerts_resolved'
    )

    class Meta:
        ordering = ['-created_at']

    def get_status_badge_class(self):
        return 'danger' if self.status == 'active' else 'success'

    def __str__(self):
        return f"SOS from {self.patient.get_full_name_or_username()} ({self.status}) at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
