from django.test import TestCase
from accounts.models import User, PatientProfile
from health.models import HealthRecord, HealthAlert, SymptomAssessment
from health.gemini_service import rule_based_symptom_triage, assess_symptoms_with_gemini
from appointments.models import Notification


class HealthModuleTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username='healthpatient',
            password='testpassword123',
            role='patient',
            first_name='Health',
            last_name='Tester'
        )
        PatientProfile.objects.create(user=self.patient)

    def test_bmi_and_vital_status_calculations(self):
        record = HealthRecord.objects.create(
            patient=self.patient,
            weight=70.0,
            height=175.0,
            heart_rate=72,
            systolic_bp=118,
            diastolic_bp=78,
            blood_sugar=92.0,
            oxygen_saturation=99
        )
        self.assertEqual(record.calculate_bmi(), 22.9)
        self.assertEqual(record.get_bp_status()[0], 'Normal BP')
        self.assertEqual(record.get_heart_rate_status()[0], 'Normal Pulse')
        self.assertEqual(record.get_blood_sugar_status()[0], 'Normal Sugar')
        self.assertEqual(record.get_oxygen_status()[0], 'Normal Oxygen')

    def test_automated_health_alert_creation(self):
        # Create record with hypertensive and low oxygen values
        record = HealthRecord.objects.create(
            patient=self.patient,
            systolic_bp=165,
            diastolic_bp=105,
            heart_rate=125,
            oxygen_saturation=92,
            blood_sugar=240.0
        )
        alerts = record.check_and_create_alerts()
        self.assertGreaterEqual(len(alerts), 3)

        # Check HealthAlert models in DB
        db_alerts = HealthAlert.objects.filter(patient=self.patient)
        self.assertGreaterEqual(db_alerts.count(), 3)

        # Check that notifications were created
        notifs = Notification.objects.filter(user=self.patient, notification_type='health_alert')
        self.assertGreaterEqual(notifs.count(), 3)

    def test_rule_based_symptom_triage(self):
        # Test Cardiology matching
        res_cardio = rule_based_symptom_triage("chest pain and palpitations", "1-3 days", "severe")
        self.assertEqual(res_cardio['recommended_specialization'], 'Cardiology')
        self.assertEqual(res_cardio['urgency_level'], 'urgent')

        # Test Dermatology matching
        res_derm = rule_based_symptom_triage("red itching skin rash on arm", "1 week", "mild")
        self.assertEqual(res_derm['recommended_specialization'], 'Dermatology')
        self.assertEqual(res_derm['urgency_level'], 'routine')

        # Test Emergency Red Flag detection
        res_emer = rule_based_symptom_triage("crushing chest pain difficulty breathing", "<24 hours", "severe")
        self.assertEqual(res_emer['urgency_level'], 'emergency')
