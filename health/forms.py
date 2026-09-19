from django import forms
from .models import HealthRecord, SymptomAssessment


class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = [
            'heart_rate', 'systolic_bp', 'diastolic_bp', 'blood_sugar',
            'weight', 'height', 'temperature', 'oxygen_saturation', 'notes'
        ]
        widgets = {
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 72',
                'min': '30',
                'max': '250'
            }),
            'systolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 120',
                'min': '50',
                'max': '260'
            }),
            'diastolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 80',
                'min': '30',
                'max': '160'
            }),
            'blood_sugar': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 95.0',
                'step': '0.1',
                'min': '20',
                'max': '600'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 68.5',
                'step': '0.1',
                'min': '10',
                'max': '350'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 172.0',
                'step': '0.5',
                'min': '40',
                'max': '250'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 98.6',
                'step': '0.1',
                'min': '90',
                'max': '110'
            }),
            'oxygen_saturation': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 98',
                'min': '50',
                'max': '100'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'How are you feeling today? Any specific symptoms or medications taken?'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Ensure at least one vital metric is filled
        metrics = [
            cleaned_data.get('heart_rate'),
            cleaned_data.get('systolic_bp'),
            cleaned_data.get('diastolic_bp'),
            cleaned_data.get('blood_sugar'),
            cleaned_data.get('weight'),
            cleaned_data.get('height'),
            cleaned_data.get('temperature'),
            cleaned_data.get('oxygen_saturation'),
        ]
        if not any(m is not None for m in metrics):
            raise forms.ValidationError("Please provide at least one vital measurement.")

        sys = cleaned_data.get('systolic_bp')
        dia = cleaned_data.get('diastolic_bp')
        if (sys and not dia) or (dia and not sys):
            raise forms.ValidationError("Please provide both Systolic and Diastolic values for Blood Pressure.")
        if sys and dia and sys <= dia:
            raise forms.ValidationError("Systolic BP must be greater than Diastolic BP.")

        return cleaned_data


class SymptomAssessmentForm(forms.ModelForm):
    DURATION_CHOICES = (
        ('Less than 24 hours', 'Less than 24 hours (Sudden / Recent onset)'),
        ('1 to 3 days', '1 to 3 days'),
        ('4 to 7 days', '4 to 7 days (About a week)'),
        ('1 to 2 weeks', '1 to 2 weeks'),
        ('More than 2 weeks', 'More than 2 weeks (Persistent / Chronic)'),
    )

    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = SymptomAssessment
        fields = ['symptoms', 'duration', 'severity', 'additional_info']
        widgets = {
            'symptoms': forms.HiddenInput(),  # Handled interactively via JS chips or direct input
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any relevant details, e.g. known allergies, medications currently taking, triggers, or pre-existing conditions...'
            }),
        }
