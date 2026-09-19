from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, PatientProfile, DoctorProfile


class AccountsModelAndAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpassword123',
            role='patient',
            first_name='Test',
            last_name='Patient'
        )
        PatientProfile.objects.create(user=self.patient_user)

        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpassword123',
            role='doctor',
            first_name='Doctor',
            last_name='Specialist'
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            qualification='MD',
            experience_years=5,
            hospital_or_clinic='General Hospital',
            consultation_fee=60.00
        )

        self.admin_user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpassword123',
            role='admin'
        )

    def test_user_role_properties(self):
        self.assertTrue(self.patient_user.is_patient)
        self.assertFalse(self.patient_user.is_doctor)

        self.assertTrue(self.doctor_user.is_doctor)
        self.assertFalse(self.doctor_user.is_patient)

        self.assertTrue(self.admin_user.is_administrator)

    def test_login_and_role_redirect(self):
        # Login as patient
        login_success = self.client.login(username='testpatient', password='testpassword123')
        self.assertTrue(login_success)
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('patient_dashboard'))

        # Access doctor dashboard as patient should be blocked
        doc_resp = self.client.get(reverse('doctor_dashboard'))
        self.assertRedirects(doc_resp, reverse('patient_dashboard'))

        self.client.logout()

        # Login as doctor
        self.client.login(username='testdoctor', password='testpassword123')
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('doctor_dashboard'))

    def test_dedicated_doctor_login_success(self):
        response = self.client.post(reverse('doctor_login'), {
            'username': 'testdoctor',
            'password': 'testpassword123',
        })
        self.assertRedirects(response, reverse('doctor_dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.doctor_user.id)

    def test_dedicated_doctor_login_rejects_patient(self):
        response = self.client.post(reverse('doctor_login'), {
            'username': 'testpatient',
            'password': 'testpassword123',
        })
        # Should stay on doctor login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access restricted")
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dedicated_admin_login_success(self):
        response = self.client.post(reverse('admin_login'), {
            'username': 'testadmin',
            'password': 'testpassword123',
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.admin_user.id)

    def test_dedicated_admin_login_rejects_non_admin(self):
        # Patient attempt
        response = self.client.post(reverse('admin_login'), {
            'username': 'testpatient',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access restricted")
        self.assertNotIn('_auth_user_id', self.client.session)

        # Doctor attempt
        doc_resp = self.client.post(reverse('admin_login'), {
            'username': 'testdoctor',
            'password': 'testpassword123',
        })
        self.assertEqual(doc_resp.status_code, 200)
        self.assertContains(doc_resp, "Access restricted")
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_role_based_access_controls(self):
        # 1. Patient trying to access admin pages
        self.client.login(username='testpatient', password='testpassword123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(resp, reverse('patient_dashboard'))

        resp = self.client.get(reverse('admin_patient_management'))
        self.assertRedirects(resp, reverse('patient_dashboard'))
        self.client.logout()

        # 2. Doctor trying to access admin pages
        self.client.login(username='testdoctor', password='testpassword123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(resp, reverse('doctor_dashboard'))
        self.client.logout()

        # 3. Admin accessing admin dashboard
        self.client.login(username='testadmin', password='testpassword123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_patient_registration(self):
        response = self.client.post(reverse('patient_register'), {
            'username': 'newpatient',
            'email': 'newpatient@example.com',
            'password': 'safePassword123',
            'confirm_password': 'safePassword123',
            'first_name': 'New',
            'last_name': 'User',
            'phone_number': '+1234567890',
            'gender': 'male',
            'blood_group': 'B+',
        })
        self.assertRedirects(response, reverse('patient_dashboard'))
        self.assertTrue(User.objects.filter(username='newpatient').exists())
        new_u = User.objects.get(username='newpatient')
        self.assertTrue(hasattr(new_u, 'patient_profile'))
