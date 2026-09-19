def user_context(request):
    """
    Context processor to inject common user state across all templates.
    """
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
            'user_role': None,
        }

    from appointments.models import Notification

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    recent = Notification.objects.filter(user=request.user)[:5]

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent,
        'user_role': getattr(request.user, 'role', 'patient'),
        'is_patient_user': getattr(request.user, 'is_patient', False),
        'is_doctor_user': getattr(request.user, 'is_doctor', False),
        'is_admin_user': getattr(request.user, 'is_administrator', False),
    }
