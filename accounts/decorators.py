from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in as a patient to access this page.")
            return redirect('login')
        if not request.user.is_patient:
            messages.error(request, "Access restricted: This area is reserved for patients.")
            if request.user.is_doctor:
                return redirect('doctor_dashboard')
            elif request.user.is_administrator:
                return redirect('admin_dashboard')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in as a doctor to access this portal.")
            return redirect('doctor_login')
        if not request.user.is_doctor:
            messages.error(request, "Access restricted: This portal is for registered healthcare providers only.")
            if request.user.is_patient:
                return redirect('patient_dashboard')
            elif request.user.is_administrator:
                return redirect('admin_dashboard')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with administrative privileges.")
            return redirect('admin_login')
        if not request.user.is_administrator:
            messages.error(request, "Access restricted: Administrative privileges required.")
            if request.user.is_doctor:
                return redirect('doctor_dashboard')
            elif request.user.is_patient:
                return redirect('patient_dashboard')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
