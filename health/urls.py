from django.urls import path
from . import views

urlpatterns = [
    path('vitals/add/', views.health_entry_view, name='health_entry'),
    path('history/', views.health_history_view, name='health_history'),
    path('trends/', views.health_trends_view, name='health_trends'),
    path('alerts/', views.health_alerts_view, name='health_alerts'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert_view, name='resolve_alert'),
    path('assessment/', views.symptom_assessment_view, name='symptom_assessment'),
    path('assessment/<int:assessment_id>/', views.assessment_result_view, name='assessment_result'),
    path('recommendations/', views.doctor_recommendations_view, name='doctor_recommendations'),
    path('summary/', views.personal_health_summary_view, name='health_summary'),
    path('chatbot/', views.chatbot_api_view, name='chatbot_api'),
    path('sos/', views.trigger_sos_view, name='trigger_sos'),
    path('emergency-alerts/', views.emergency_alerts_view, name='emergency_alerts'),
    path('emergency-alerts/<int:alert_id>/resolve/', views.resolve_sos_view, name='resolve_sos'),
    path('timeline/', views.health_timeline_view, name='health_timeline'),
    path('risk-score/', views.health_risk_score_view, name='health_risk_score'),
]

