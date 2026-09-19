from datetime import date, time, timedelta
from django.test import TestCase, Client
from django.utils import timezone
from accounts.models import User, DoctorProfile, PatientProfile
from appointments.models import Appointment, ConsultationRecord


class AppointmentAndQueueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient1 = User.objects.create_user(username='apt_patient1', password='pass', role='patient')
        PatientProfile.objects.create(user=self.patient1)

        self.patient2 = User.objects.create_user(username='apt_patient2', password='pass', role='patient')
        PatientProfile.objects.create(user=self.patient2)

        self.doctor_user = User.objects.create_user(username='apt_doctor', password='pass', role='doctor')
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            qualification='MD',
            slot_duration_minutes=20,
            start_time=time(9, 0),
            end_time=time(17, 0),
            available_days='Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday'
        )

    def test_appointment_id_generation(self):
        appt = Appointment.objects.create(
            patient=self.patient1,
            doctor=self.doctor,
            appointment_date=timezone.now().date() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit='General checkup'
        )
        self.assertTrue(appt.appointment_id.startswith('APT-'))

    def test_queue_position_and_wait_time(self):
        test_date = timezone.now().date() + timedelta(days=2)

        apt1 = Appointment.objects.create(
            patient=self.patient1,
            doctor=self.doctor,
            appointment_date=test_date,
            appointment_time=time(9, 0),
            reason_for_visit='First in line',
            status='approved'
        )

        apt2 = Appointment.objects.create(
            patient=self.patient2,
            doctor=self.doctor,
            appointment_date=test_date,
            appointment_time=time(9, 30),
            reason_for_visit='Second in line',
            status='approved'
        )

        q1 = apt1.get_queue_info()
        self.assertEqual(q1['queue_position'], 1)
        self.assertEqual(q1['patients_ahead'], 0)
        self.assertEqual(q1['estimated_wait_time_minutes'], 0)

        q2 = apt2.get_queue_info()
        self.assertEqual(q2['queue_position'], 2)
        self.assertEqual(q2['patients_ahead'], 1)
        self.assertEqual(q2['estimated_wait_time_minutes'], 20) # 1 patient ahead * 20 mins

    def test_consultation_creation(self):
        test_date = timezone.now().date()
        apt = Appointment.objects.create(
            patient=self.patient1,
            doctor=self.doctor,
            appointment_date=test_date,
            appointment_time=time(11, 0),
            reason_for_visit='Hypertension consult',
            status='approved'
        )

        record = ConsultationRecord.objects.create(
            appointment=apt,
            patient=self.patient1,
            doctor=self.doctor,
            diagnosis='Essential Hypertension',
            clinical_notes='Reduce sodium intake.',
            prescription_items='Lisinopril 10mg | 1 tab | Daily | 30 days'
        )
        self.assertEqual(apt.consultation_record, record)
        self.assertIn('Lisinopril', record.prescription_items)
