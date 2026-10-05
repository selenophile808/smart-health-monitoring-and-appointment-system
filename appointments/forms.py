from django import forms
from django.utils import timezone
from .models import Appointment, ConsultationRecord, Review
from accounts.models import DoctorProfile


class AppointmentBookingForm(forms.ModelForm):
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.localdate().strftime('%Y-%m-%d')
        })
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason_for_visit', 'notes']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'reason_for_visit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary reason or complaint for consultation'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional context, current symptoms, questions for the doctor...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = DoctorProfile.objects.filter(
            is_available=True,
            is_approved_by_admin=True
        ).select_related('user')
        # Show each doctor's live status (Available / Busy / Offline) in the dropdown,
        # so the patient can see it before booking.
        self.fields['doctor'].label_from_instance = (
            lambda doc: f"{doc} - {doc.get_current_status_display()}"
        )

    def clean_appointment_date(self):
        appt_date = self.cleaned_data.get('appointment_date')
        if appt_date and appt_date < timezone.localdate():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appt_date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appt_date = cleaned_data.get('appointment_date')
        appt_time = cleaned_data.get('appointment_time')

        if doctor and appt_date and appt_time:
            # Check weekday availability
            day_name = appt_date.strftime('%A')
            available_days = doctor.get_available_days_list()
            if available_days and day_name not in available_days:
                raise forms.ValidationError(
                    f"Dr. {doctor.user.get_full_name_or_username()} is not available on {day_name}s. Available days: {', '.join(available_days)}."
                )

            # Check double booking
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appt_date,
                appointment_time=appt_time,
                status__in=['pending', 'approved', 'in_progress']
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    "This time slot is already booked or reserved. Please choose another time slot."
                )

        return cleaned_data


class ConsultationRecordForm(forms.ModelForm):
    follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().strftime('%Y-%m-%d')
        })
    )

    class Meta:
        model = ConsultationRecord
        fields = [
            'diagnosis', 'symptoms_observed', 'clinical_notes',
            'prescription_items', 'recommended_tests', 'follow_up_date'
        ]
        widgets = {
            'diagnosis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary Diagnosis / Clinical findings'
            }),
            'symptoms_observed': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Symptoms reported by patient and clinical observations'
            }),
            'clinical_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed clinical impressions, diet recommendations, physical precautions...'
            }),
            'prescription_items': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 4,
                'placeholder': "Medicine Name | Dosage | Frequency | Duration | Special Instructions\nExample:\nAmoxicillin 500mg | 1 cap | Three times daily (after meals) | 5 days | Complete full course\nParacetamol 650mg | 1 tab | SOS for fever/pain (max 3/day) | 3 days | As needed"
            }),
            'recommended_tests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Recommended diagnostic investigations (e.g. Complete Blood Count, ECG, Chest X-Ray)'
            }),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=Review.RATING_CHOICES, attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share your experience with this doctor (optional)'
            }),
        }
