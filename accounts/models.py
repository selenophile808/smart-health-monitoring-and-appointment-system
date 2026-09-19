from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    )

    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    @property
    def is_patient(self):
        return self.role == 'patient'

    @property
    def is_doctor(self):
        return self.role == 'doctor'

    @property
    def is_administrator(self):
        return self.role == 'admin' or self.is_superuser or self.is_staff

    def get_full_name_or_username(self):
        name = self.get_full_name()
        return name if name else self.username

    def __str__(self):
        role_label = dict(self.ROLE_CHOICES).get(self.role, self.role).capitalize()
        return f"{self.get_full_name_or_username()} ({role_label})"


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True, help_text="Known past medical history, surgeries, etc.")
    allergies = models.TextField(blank=True, null=True, help_text="Drug or food allergies")
    chronic_conditions = models.TextField(blank=True, null=True, help_text="E.g. Diabetes, Hypertension, Asthma")
    current_medications = models.TextField(blank=True, null=True, help_text="Any ongoing medications")

    def __str__(self):
        return f"Patient: {self.user.get_full_name_or_username()}"


class DoctorProfile(models.Model):
    SPECIALIZATION_CHOICES = (
        ('General Medicine', 'General Medicine / Physician'),
        ('Cardiology', 'Cardiology (Heart & Blood Vessels)'),
        ('Dermatology', 'Dermatology (Skin, Hair, Nails)'),
        ('Neurology', 'Neurology (Brain & Nervous System)'),
        ('Orthopedics', 'Orthopedics (Bones & Joints)'),
        ('Pediatrics', 'Pediatrics (Children Health)'),
        ('Pulmonology', 'Pulmonology (Lungs & Respiratory)'),
        ('Gastroenterology', 'Gastroenterology (Digestive System)'),
        ('Endocrinology', 'Endocrinology (Diabetes & Hormones)'),
        ('Psychiatry', 'Psychiatry & Mental Health'),
        ('ENT', 'ENT (Ear, Nose & Throat)'),
        ('Ophthalmology', 'Ophthalmology (Eye Care)'),
        ('Gynecology', 'Gynecology & Obstetrics'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES, default='General Medicine')
    qualification = models.CharField(max_length=150, help_text="E.g., MBBS, MD, MS, FACC")
    experience_years = models.PositiveIntegerField(default=1)
    hospital_or_clinic = models.CharField(max_length=200, help_text="Hospital or Clinic Name")
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    bio = models.TextField(blank=True, null=True)
    available_days = models.CharField(
        max_length=200,
        default="Monday, Tuesday, Wednesday, Thursday, Friday",
        help_text="Comma-separated days doctor is available"
    )
    start_time = models.TimeField(default="09:00:00")
    end_time = models.TimeField(default="17:00:00")
    slot_duration_minutes = models.PositiveIntegerField(default=30)
    is_available = models.BooleanField(default=True)
    is_approved_by_admin = models.BooleanField(default=True)

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    )
    current_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    def get_available_days_list(self):
        return [d.strip() for d in self.available_days.split(',') if d.strip()]

    def get_status_badge_class(self):
        return {'available': 'success', 'busy': 'warning', 'offline': 'secondary'}.get(self.current_status, 'secondary')

    def get_average_rating(self):
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else None

    def get_review_count(self):
        return self.reviews.count()

    def __str__(self):
        return f"Dr. {self.user.get_full_name_or_username()} ({self.specialization})"
