from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, PatientProfile, DoctorProfile
from health.models import HealthRecord, HealthAlert, SymptomAssessment
from appointments.models import Appointment, ConsultationRecord, Notification


class Command(BaseCommand):
    help = 'Populates the database with realistic demonstration data for patients, doctors, vitals, appointments, and prescriptions.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding demonstration data..."))

        # 1. Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smarthealth.local',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Admin: admin / admin123"))

        # 2. Doctors
        doctors_data = [
            {
                'username': 'dr_sarah',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah.johnson@stjudes.org',
                'specialization': 'Cardiology',
                'qualification': 'MD, FACC, Harvard Medical School',
                'experience_years': 14,
                'hospital_or_clinic': 'Metro Cardiovascular Institute',
                'consultation_fee': 75.00,
                'available_days': 'Monday, Tuesday, Wednesday, Thursday, Friday',
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'slot_duration_minutes': 30,
                'bio': 'Board-certified cardiologist specializing in preventive cardiovascular wellness, hypertension management, and echocardiography.',
            },
            {
                'username': 'dr_chen',
                'first_name': 'Robert',
                'last_name': 'Chen',
                'email': 'r.chen@cityhealth.org',
                'specialization': 'General Medicine',
                'qualification': 'MBBS, MD (Internal Medicine)',
                'experience_years': 10,
                'hospital_or_clinic': 'Downtown Health Pavilion',
                'consultation_fee': 50.00,
                'available_days': 'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday',
                'start_time': time(8, 30),
                'end_time': time(16, 30),
                'slot_duration_minutes': 20,
                'bio': 'Primary care physician committed to holistic adult health, early disease detection, and chronic lifestyle condition management.',
            },
            {
                'username': 'dr_emily',
                'first_name': 'Emily',
                'last_name': 'Davis',
                'email': 'emily.davis@skincareclinic.com',
                'specialization': 'Dermatology',
                'qualification': 'MD, FAAD (Johns Hopkins)',
                'experience_years': 8,
                'hospital_or_clinic': 'Aura Dermatology Center',
                'consultation_fee': 65.00,
                'available_days': 'Monday, Wednesday, Friday',
                'start_time': time(10, 0),
                'end_time': time(18, 0),
                'slot_duration_minutes': 25,
                'bio': 'Specialist in clinical dermatology, cutaneous allergic conditions, eczema, psoriasis, and dermatoscopic examinations.',
            }
        ]

        created_doctors = []
        for d_info in doctors_data:
            doc_user, created = User.objects.get_or_create(
                username=d_info['username'],
                defaults={
                    'first_name': d_info['first_name'],
                    'last_name': d_info['last_name'],
                    'email': d_info['email'],
                    'role': 'doctor',
                    'phone_number': '+1 (555) 234-8901',
                    'address': d_info['hospital_or_clinic'],
                }
            )
            if created:
                doc_user.set_password('doctor123')
                doc_user.save()

            doc_profile, p_created = DoctorProfile.objects.get_or_create(
                user=doc_user,
                defaults={
                    'specialization': d_info['specialization'],
                    'qualification': d_info['qualification'],
                    'experience_years': d_info['experience_years'],
                    'hospital_or_clinic': d_info['hospital_or_clinic'],
                    'consultation_fee': d_info['consultation_fee'],
                    'available_days': d_info['available_days'],
                    'start_time': d_info['start_time'],
                    'end_time': d_info['end_time'],
                    'slot_duration_minutes': d_info['slot_duration_minutes'],
                    'bio': d_info['bio'],
                    'is_available': True,
                    'is_approved_by_admin': True,
                }
            )
            created_doctors.append(doc_profile)
            self.stdout.write(self.style.SUCCESS(f"Created Doctor: {doc_user.username} / doctor123 ({d_info['specialization']})"))

        # 3. Patients
        patient1_user, p1_created = User.objects.get_or_create(
            username='patient1',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'role': 'patient',
                'phone_number': '+1 (555) 987-6543',
                'gender': 'male',
                'blood_group': 'O+',
                'date_of_birth': date(1988, 5, 14),
                'address': '742 Evergreen Terrace, Springfield',
            }
        )
        if p1_created:
            patient1_user.set_password('patient123')
            patient1_user.save()
            PatientProfile.objects.create(
                user=patient1_user,
                emergency_contact_name='Mary Doe',
                emergency_contact_phone='+1 (555) 987-0000',
                allergies='Penicillin, Shellfish',
                chronic_conditions='Mild Hypertension',
                current_medications='Amlodipine 5mg OD',
                medical_history='Appendectomy in 2015'
            )
            self.stdout.write(self.style.SUCCESS("Created Patient: patient1 / patient123"))

        patient2_user, p2_created = User.objects.get_or_create(
            username='patient2',
            defaults={
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com',
                'role': 'patient',
                'phone_number': '+1 (555) 345-6789',
                'gender': 'female',
                'blood_group': 'A+',
                'date_of_birth': date(1992, 9, 21),
                'address': '124 Conch Street, Pacific City',
            }
        )
        if p2_created:
            patient2_user.set_password('patient123')
            patient2_user.save()
            PatientProfile.objects.create(
                user=patient2_user,
                emergency_contact_name='David Smith',
                emergency_contact_phone='+1 (555) 345-0000',
                allergies='None known',
                chronic_conditions='None'
            )
            self.stdout.write(self.style.SUCCESS("Created Patient: patient2 / patient123"))

        # 4. Health Records for Patient 1 (Series of historical vitals)
        now = timezone.now()
        vitals_data = [
            {'offset': 6, 'hr': 74, 'sys': 122, 'dia': 78, 'sugar': 92.0, 'weight': 76.5, 'spo2': 99, 'temp': 98.4},
            {'offset': 5, 'hr': 78, 'sys': 128, 'dia': 82, 'sugar': 98.0, 'weight': 76.3, 'spo2': 98, 'temp': 98.6},
            {'offset': 4, 'hr': 82, 'sys': 134, 'dia': 86, 'sugar': 105.0, 'weight': 76.0, 'spo2': 98, 'temp': 98.6},
            {'offset': 3, 'hr': 85, 'sys': 142, 'dia': 92, 'sugar': 110.0, 'weight': 75.8, 'spo2': 97, 'temp': 98.8}, # Triggered alert
            {'offset': 2, 'hr': 80, 'sys': 136, 'dia': 88, 'sugar': 99.0, 'weight': 75.9, 'spo2': 98, 'temp': 98.5},
            {'offset': 1, 'hr': 76, 'sys': 130, 'dia': 84, 'sugar': 95.0, 'weight': 75.5, 'spo2': 98, 'temp': 98.4},
            {'offset': 0, 'hr': 75, 'sys': 126, 'dia': 80, 'sugar': 94.0, 'weight': 75.4, 'spo2': 99, 'temp': 98.6},
        ]

        if not HealthRecord.objects.filter(patient=patient1_user).exists():
            for v in vitals_data:
                rec_dt = now - timedelta(days=v['offset'], hours=2)
                hr_rec = HealthRecord.objects.create(
                    patient=patient1_user,
                    recorded_at=rec_dt,
                    heart_rate=v['hr'],
                    systolic_bp=v['sys'],
                    diastolic_bp=v['dia'],
                    blood_sugar=v['sugar'],
                    weight=v['weight'],
                    height=178.0,
                    oxygen_saturation=v['spo2'],
                    temperature=v['temp'],
                    notes='Routine daily morning measurement.'
                )
                if v['sys'] >= 140:
                    hr_rec.check_and_create_alerts()

            self.stdout.write(self.style.SUCCESS("Created 7 days of historical vitals and alerts for patient1."))

        # 5. Symptom Assessment
        if not SymptomAssessment.objects.filter(patient=patient1_user).exists():
            SymptomAssessment.objects.create(
                patient=patient1_user,
                symptoms='Occasional chest tightness, palpitations during climbing stairs, mild fatigue',
                duration='4 to 7 days',
                severity='moderate',
                additional_info='Mild family history of cardiovascular condition.',
                ai_response_raw='Generated via demonstration clinical triage engine.',
                possible_concerns='Cardiovascular exertion response, mild hemodynamic strain.',
                recommended_specialization='Cardiology',
                urgency_level='consult_soon',
                guidance_notes='Avoid high-intensity aerobic exertion. Record resting blood pressure twice daily. Schedule consultation with a cardiologist for ECG and clinical review.'
            )
            self.stdout.write(self.style.SUCCESS("Created demonstration AI symptom assessment."))

        # 6. Appointments & Completed Consultation
        dr_cardio = created_doctors[0]
        dr_general = created_doctors[1]
        today = timezone.now().date()

        # Completed Appointment in the past
        past_date = today - timedelta(days=5)
        apt_completed, c_created = Appointment.objects.get_or_create(
            appointment_id=f"APT-{past_date.strftime('%Y%m%d')}-SAMPLE1",
            defaults={
                'patient': patient1_user,
                'doctor': dr_cardio,
                'appointment_date': past_date,
                'appointment_time': time(10, 0),
                'reason_for_visit': 'Cardiology evaluation for elevated blood pressure and palpitations',
                'status': 'completed',
            }
        )

        if c_created:
            ConsultationRecord.objects.create(
                appointment=apt_completed,
                patient=patient1_user,
                doctor=dr_cardio,
                visit_date=past_date,
                diagnosis='Stage 1 Essential Hypertension (ICD-10 I10) with mild exertion tachycardia',
                symptoms_observed='Patient reports mild chest tightness on stairs. Resting BP 138/88 mmHg, regular pulse.',
                clinical_notes='Cardiac auscultation normal S1/S2 without murmurs. Recommended salt restriction (<2g/day), 30 mins brisk walking daily, and follow-up in 4 weeks.',
                prescription_items=(
                    "Telmisartan 40mg | 1 tablet | Once daily (morning, after breakfast) | 30 days | Take regularly at fixed time\n"
                    "Metoprolol Tartrate 25mg | 1/2 tablet | Twice daily | 14 days | Monitor heart rate"
                ),
                recommended_tests='12-Lead Electrocardiogram (ECG), Serum Lipid Profile, Serum Creatinine',
                follow_up_date=today + timedelta(days=25)
            )
            self.stdout.write(self.style.SUCCESS("Created past completed appointment & electronic prescription."))

        # Today's Scheduled Appointment for Live Queue demonstration
        apt_today1, _ = Appointment.objects.get_or_create(
            appointment_id=f"APT-{today.strftime('%Y%m%d')}-QUEUE1",
            defaults={
                'patient': patient2_user,
                'doctor': dr_cardio,
                'appointment_date': today,
                'appointment_time': time(10, 0),
                'reason_for_visit': 'Heart murmur checkup and routine ECG',
                'status': 'in_progress',
            }
        )

        apt_today2, _ = Appointment.objects.get_or_create(
            appointment_id=f"APT-{today.strftime('%Y%m%d')}-QUEUE2",
            defaults={
                'patient': patient1_user,
                'doctor': dr_cardio,
                'appointment_date': today,
                'appointment_time': time(10, 30),
                'reason_for_visit': 'Follow-up blood pressure review and medication efficacy check',
                'status': 'approved',
            }
        )

        self.stdout.write(self.style.SUCCESS("Created active today appointments for live queue testing."))

        self.stdout.write(self.style.SUCCESS("=== SEEDING COMPLETE! ==="))
        self.stdout.write("Credentials:")
        self.stdout.write(" - Admin: admin / admin123")
        self.stdout.write(" - Doctor (Cardiology): dr_sarah / doctor123")
        self.stdout.write(" - Doctor (General Med): dr_chen / doctor123")
        self.stdout.write(" - Patient 1 (has vitals & queue): patient1 / patient123")
        self.stdout.write(" - Patient 2: patient2 / patient123")
