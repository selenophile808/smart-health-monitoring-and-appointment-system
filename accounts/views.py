from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from .forms import (
    PatientRegistrationForm,
    DoctorRegistrationForm,
    UserProfileUpdateForm,
    PatientProfileUpdateForm,
    DoctorProfileUpdateForm,
    ForgotPasswordResetForm
)
from appointments.models import Notification

User = get_user_model()


def dashboard_redirect(request):
    """
    Redirects authenticated users to their corresponding dashboard based on role.
    """
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_patient:
        return redirect('patient_dashboard')
    elif request.user.is_doctor:
        return redirect('doctor_dashboard')
    elif request.user.is_administrator:
        return redirect('admin_dashboard')
    return redirect('home')


def login_view(request):
    if request.user.is_authenticated:
        return dashboard_redirect(request)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name_or_username()}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return dashboard_redirect(request)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def doctor_login_view(request):
    """
    Dedicated login portal for healthcare providers.
    """
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor_dashboard')
        return dashboard_redirect(request)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_doctor:
                messages.error(
                    request,
                    "Access restricted: This portal is reserved for registered healthcare providers. "
                    "If you are a patient or administrator, please use your dedicated login portal."
                )
                return render(request, 'accounts/doctor_login.html', {'form': form})
            login(request, user)
            messages.success(request, f"Welcome back, Dr. {user.get_full_name_or_username()}! Logged into Clinical Portal.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('doctor_dashboard')
        else:
            messages.error(request, "Invalid doctor credentials. Please check your username and password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/doctor_login.html', {'form': form})


def admin_login_view(request):
    """
    Dedicated login portal for system administrators.
    """
    if request.user.is_authenticated:
        if request.user.is_administrator:
            return redirect('admin_dashboard')
        return dashboard_redirect(request)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_administrator:
                messages.error(
                    request,
                    "Access restricted: Administrative credentials required to access this console."
                )
                return render(request, 'accounts/admin_login.html', {'form': form})
            login(request, user)
            messages.success(request, f"Welcome to the System Admin Console, {user.get_full_name_or_username()}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid administrator credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/admin_login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


def patient_register_view(request):
    if request.user.is_authenticated:
        return dashboard_redirect(request)

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, "Welcome! Your patient profile has been registered successfully.")
            return redirect('patient_dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/patient_register.html', {'form': form})


def doctor_register_view(request):
    if request.user.is_authenticated:
        return dashboard_redirect(request)

    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
            messages.success(request, "Doctor registration submitted successfully! Welcome to the medical network.")
            return redirect('doctor_dashboard')
        else:
            messages.error(request, "Please correct the errors below to register as a doctor.")
    else:
        form = DoctorRegistrationForm()

    return render(request, 'accounts/doctor_register.html', {'form': form})


@login_required
def profile_view(request):
    user = request.user
    user_form = UserProfileUpdateForm(instance=user)
    patient_form = None
    doctor_form = None

    if user.is_patient and hasattr(user, 'patient_profile'):
        patient_form = PatientProfileUpdateForm(instance=user.patient_profile)
    elif user.is_doctor and hasattr(user, 'doctor_profile'):
        doctor_form = DoctorProfileUpdateForm(instance=user.doctor_profile)

    if request.method == 'POST':
        user_form = UserProfileUpdateForm(request.POST, request.FILES, instance=user)
        is_valid = user_form.is_valid()

        if user.is_patient and hasattr(user, 'patient_profile'):
            patient_form = PatientProfileUpdateForm(request.POST, instance=user.patient_profile)
            if patient_form.is_valid() and is_valid:
                user_form.save()
                patient_form.save()
                messages.success(request, "Your profile has been updated successfully.")
                return redirect('profile')

        elif user.is_doctor and hasattr(user, 'doctor_profile'):
            doctor_form = DoctorProfileUpdateForm(request.POST, instance=user.doctor_profile)
            if doctor_form.is_valid() and is_valid:
                user_form.save()
                doctor_form.save()
                messages.success(request, "Your doctor profile and availability have been updated.")
                return redirect('profile')

        elif is_valid:
            user_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'patient_form': patient_form,
        'doctor_form': doctor_form,
    })


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('notifications_list')


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications_list')


def forgot_password_view(request):
    """
    Self-service secure account password reset flow.
    """
    if request.user.is_authenticated:
        return dashboard_redirect(request)

    if request.method == 'POST':
        form = ForgotPasswordResetForm(request.POST)
        if form.is_valid():
            ident = form.cleaned_data['username_or_email'].strip()
            new_password = form.cleaned_data['new_password']

            user = User.objects.filter(Q(username=ident) | Q(email__iexact=ident)).first()
            if user:
                user.set_password(new_password)
                user.save()
                messages.success(request, f"Password successfully updated for {user.username}! Please sign in below.")
                if user.is_doctor:
                    return redirect('doctor_login')
                elif user.is_administrator:
                    return redirect('admin_login')
                else:
                    return redirect('login')
            else:
                messages.error(request, "No registered account found with that username or email address.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ForgotPasswordResetForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})

