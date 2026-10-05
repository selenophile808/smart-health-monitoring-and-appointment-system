from datetime import time
from django.core.management.base import BaseCommand
from accounts.models import User, DoctorProfile
from accounts.utils import generate_avatar


DOCTORS = [
    ('dr_arun', 'Arun', 'Kumar', 'Neurology', 'MBBS, DM (Neurology)', 12, 'Brain & Spine Institute', 80,
     'Neurologist for headaches, migraine, epilepsy and stroke recovery.'),
    ('dr_priya', 'Priya', 'Raman', 'Orthopedics', 'MBBS, MS (Orthopedics)', 9, 'Bone & Joint Care Center', 70,
     'Orthopedic surgeon for joint pain, fractures and sports injuries.'),
    ('dr_karthik', 'Karthik', 'Subramanian', 'Pediatrics', 'MBBS, MD (Pediatrics)', 11, "Little Stars Children's Clinic", 45,
     'Child specialist for fever, vaccination, growth and nutrition.'),
    ('dr_lakshmi', 'Lakshmi', 'Narayan', 'Pulmonology', 'MBBS, MD (Pulmonary Medicine)', 10, 'Lung Care Hospital', 60,
     'Lung specialist for asthma, chronic cough and breathing problems.'),
    ('dr_vikram', 'Vikram', 'Singh', 'Gastroenterology', 'MBBS, DM (Gastroenterology)', 13, 'Digestive Health Center', 75,
     'Digestive specialist for acidity, liver and stomach problems.'),
    ('dr_anita', 'Anita', 'Desai', 'Endocrinology', 'MBBS, MD, DM (Endocrinology)', 15, 'Diabetes & Hormone Clinic', 85,
     'Diabetes, thyroid and hormone specialist.'),
    ('dr_rahul', 'Rahul', 'Menon', 'Psychiatry', 'MBBS, MD (Psychiatry)', 8, 'Mind Care Center', 65,
     'Psychiatrist for stress, anxiety, sleep and mental wellbeing.'),
    ('dr_divya', 'Divya', 'Iyer', 'ENT', 'MBBS, MS (ENT)', 7, 'ENT Care Hospital', 55,
     'Ear, nose and throat specialist for sinus, throat and hearing problems.'),
    ('dr_suresh', 'Suresh', 'Babu', 'Ophthalmology', 'MBBS, MS (Ophthalmology)', 14, 'Vision Eye Hospital', 60,
     'Eye specialist for vision problems, cataract and eye infections.'),
    ('dr_kavya', 'Kavya', 'Nair', 'Gynecology', 'MBBS, MD (Obstetrics & Gynecology)', 12, "Women's Health Center", 70,
     "Women's health specialist for pregnancy care and gynecology."),
]


class Command(BaseCommand):
    help = 'Adds one demo doctor for every remaining specialization. Safe to run many times.'

    def handle(self, *args, **options):
        added = 0
        for username, first, last, spec, qual, years, hospital, fee, bio in DOCTORS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first, 'last_name': last,
                    'email': f'{username}@smarthealth.demo',
                    'role': 'doctor',
                    'phone_number': '+91 90000 00000',
                    'address': hospital,
                }
            )
            if created:
                user.set_password('doctor123')
                user.save()
                user.profile_picture.save(f'{username}.jpg', generate_avatar(f'{first} {last}'), save=True)
            _, p_created = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'specialization': spec, 'qualification': qual, 'experience_years': years,
                    'hospital_or_clinic': hospital, 'consultation_fee': fee,
                    'available_days': 'Monday, Tuesday, Wednesday, Thursday, Friday',
                    'start_time': time(9, 0), 'end_time': time(17, 0), 'slot_duration_minutes': 30,
                    'bio': bio, 'is_available': True, 'is_approved_by_admin': True,
                }
            )
            if p_created:
                added += 1
                self.stdout.write(self.style.SUCCESS(f'Added {username} / doctor123 ({spec})'))
        self.stdout.write(self.style.SUCCESS(f'Done. {added} new doctor(s) added.'))
