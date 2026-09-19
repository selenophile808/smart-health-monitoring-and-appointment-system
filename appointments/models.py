import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved & Scheduled'),
        ('in_progress', 'In Consultation'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    appointment_id = models.CharField(max_length=40, unique=True, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    symptom_assessment = models.ForeignKey(
        'health.SymptomAssessment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason_for_visit = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=models.Q(status__in=['pending', 'approved', 'in_progress']),
                name='unique_active_doctor_slot'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            date_prefix = timezone.now().strftime('%Y%m%d')
            rand_suffix = uuid.uuid4().hex[:6].upper()
            self.appointment_id = f"APT-{date_prefix}-{rand_suffix}"
        super().save(*args, **kwargs)

    def get_status_badge_class(self):
        mapping = {
            'pending': 'warning',
            'approved': 'info',
            'in_progress': 'primary',
            'completed': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary',
        }
        return mapping.get(self.status, 'secondary')

    def get_queue_info(self):
        """
        Computes dynamic queue position and estimated waiting time.

        The queue counts EVERY active booking for this doctor on this date
        (pending + approved + in_progress), ordered by appointment time and
        then by booking order (created_at). This way a patient sees their
        real position in line as soon as they book -- they don't have to
        wait for the doctor to accept the request first for the queue count
        to reflect earlier bookings.
        """
        if self.status == 'completed':
            return {
                'queue_position': 0,
                'patients_ahead': 0,
                'estimated_wait_time_minutes': 0,
                'current_status': 'Completed',
                'last_updated': timezone.now(),
                'is_active_queue': False,
            }

        if self.status in ('rejected', 'cancelled'):
            return {
                'queue_position': '-',
                'patients_ahead': 0,
                'estimated_wait_time_minutes': 0,
                'current_status': self.get_status_display(),
                'last_updated': timezone.now(),
                'is_active_queue': False,
            }

        # Every currently active booking for this doctor/date, in line order.
        active_appointments = list(Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            status__in=['pending', 'approved', 'in_progress']
        ).order_by('appointment_time', 'created_at'))

        try:
            position = active_appointments.index(self) + 1
        except ValueError:
            # Appointment not found in the live list (e.g. stale instance) --
            # fall back to putting it at the back of the line.
            position = len(active_appointments) + 1

        patients_ahead = position - 1
        slot_duration = self.doctor.slot_duration_minutes or 20
        wait_time = patients_ahead * slot_duration

        status_label = {
            'pending': 'Awaiting Doctor Confirmation',
            'approved': 'In Queue',
            'in_progress': 'In Consultation',
        }.get(self.status, self.get_status_display())

        return {
            'queue_position': position,
            'patients_ahead': patients_ahead,
            'estimated_wait_time_minutes': wait_time,
            'current_status': status_label,
            'slot_duration': slot_duration,
            'last_updated': timezone.now(),
            'is_active_queue': True,
        }

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.get_full_name_or_username()} with Dr. {self.doctor.user.get_full_name_or_username()} ({self.appointment_date})"


class ConsultationRecord(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='consultation_record'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='consultation_records'
    )
    visit_date = models.DateField(default=timezone.now)
    diagnosis = models.TextField(help_text="Clinical findings and diagnosis")
    symptoms_observed = models.TextField(blank=True, null=True)
    clinical_notes = models.TextField(help_text="Doctor observations, clinical advice, lifestyle recommendations")
    prescription_items = models.TextField(
        help_text="Medications prescribed: Medicine Name, Dosage, Frequency, Duration, Instructions"
    )
    recommended_tests = models.TextField(blank=True, null=True, help_text="Diagnostic lab tests or imaging")
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visit_date', '-created_at']

    def __str__(self):
        return f"Record for {self.patient.get_full_name_or_username()} - {self.visit_date}"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('appointment', 'Appointment Update'),
        ('health_alert', 'Health Alert'),
        ('queue', 'Queue Update'),
        ('general', 'General Notification'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='general'
    )
    link_url = models.CharField(max_length=200, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.get_full_name_or_username()}: {self.title}"


class Review(models.Model):
    """
    A patient's rating/review of a doctor, tied to a specific completed
    appointment. Only patients who actually completed an appointment with
    that doctor may leave a review for it.
    """
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='review'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_written'
    )
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}\u2605 review by {self.patient.get_full_name_or_username()} for Dr. {self.doctor.user.get_full_name_or_username()}"
