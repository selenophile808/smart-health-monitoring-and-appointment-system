from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import PatientProfile, DoctorProfile

User = get_user_model()


class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))

    # Patient profile fields
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person name'}))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone number'}))
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Known allergies (food/drugs)'}))
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'E.g., Asthma, Diabetes, Hypertension'}))

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'gender', 'blood_group', 'address'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential address'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("An account with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 or p2:
            if p1 != p2:
                self.add_error('confirm_password', "Passwords do not match.")
            elif not p1:
                self.add_error('password', "This field is required.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            PatientProfile.objects.create(
                user=user,
                emergency_contact_name=self.cleaned_data.get('emergency_contact_name', ''),
                emergency_contact_phone=self.cleaned_data.get('emergency_contact_phone', ''),
                allergies=self.cleaned_data.get('allergies', ''),
                chronic_conditions=self.cleaned_data.get('chronic_conditions', '')
            )
        return user


class DoctorRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))

    # Doctor-specific profile fields
    specialization = forms.ChoiceField(
        choices=DoctorProfile.SPECIALIZATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    qualification = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'E.g. MBBS, MD (Cardiology)'})
    )
    experience_years = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of experience'})
    )
    hospital_or_clinic = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital or Medical Center Name'})
    )
    consultation_fee = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Consultation Fee ($)'})
    )
    available_days = forms.CharField(
        initial="Monday, Tuesday, Wednesday, Thursday, Friday",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Monday, Tuesday, Wednesday...'})
    )
    start_time = forms.TimeField(
        initial="09:00",
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    end_time = forms.TimeField(
        initial="17:00",
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    slot_duration_minutes = forms.IntegerField(
        initial=30,
        min_value=10,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Professional overview, clinical interests...'})
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'gender', 'address'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Professional email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Clinic address / City'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("An account with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 or p2:
            if p1 != p2:
                self.add_error('confirm_password', "Passwords do not match.")
            elif not p1:
                self.add_error('password', "This field is required.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'doctor'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            DoctorProfile.objects.create(
                user=user,
                specialization=self.cleaned_data.get('specialization'),
                qualification=self.cleaned_data.get('qualification'),
                experience_years=self.cleaned_data.get('experience_years', 1),
                hospital_or_clinic=self.cleaned_data.get('hospital_or_clinic'),
                consultation_fee=self.cleaned_data.get('consultation_fee', 50.00),
                available_days=self.cleaned_data.get('available_days', 'Monday, Tuesday, Wednesday, Thursday, Friday'),
                start_time=self.cleaned_data.get('start_time', '09:00'),
                end_time=self.cleaned_data.get('end_time', '17:00'),
                slot_duration_minutes=self.cleaned_data.get('slot_duration_minutes', 30),
                bio=self.cleaned_data.get('bio', ''),
                is_available=True,
                is_approved_by_admin=True
            )
        return user


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'gender', 'blood_group', 'address', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class PatientProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['emergency_contact_name', 'emergency_contact_phone', 'medical_history', 'allergies', 'chronic_conditions', 'current_medications']
        widgets = {
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'chronic_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DoctorProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = [
            'specialization', 'qualification', 'experience_years', 'hospital_or_clinic',
            'consultation_fee', 'available_days', 'start_time', 'end_time',
            'slot_duration_minutes', 'is_available', 'bio'
        ]
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'hospital_or_clinic': forms.TextInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ForgotPasswordResetForm(forms.Form):
    username_or_email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter registered username or email address'}),
        label="Username or Email"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 or p2:
            if p1 != p2:
                self.add_error('confirm_password', "Passwords do not match.")
        if p1 and len(p1) < 6:
            self.add_error('new_password', "Password must be at least 6 characters.")
        return cleaned_data

