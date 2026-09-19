import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Specialized medical categories matching DoctorProfile.SPECIALIZATION_CHOICES
SPECIALTY_CHOICES = [
    'General Medicine',
    'Cardiology',
    'Dermatology',
    'Neurology',
    'Orthopedics',
    'Pediatrics',
    'Pulmonology',
    'Gastroenterology',
    'Endocrinology',
    'Psychiatry',
    'ENT',
    'Ophthalmology',
    'Gynecology',
]


def assess_symptoms_with_gemini(symptoms_text, duration, severity, additional_info=""):
    """
    Evaluates patient symptoms using Google Gemini API if available,
    with a graceful clinical rule-based triage fallback engine.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    # Attempt Gemini API first if key exists
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # Try modern models in sequence
            model_names = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
            model = None
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    break
                except Exception:
                    continue

            if model:
                prompt = f"""
You are a preliminary healthcare triage and educational AI assistant inside a hospital management system.
A patient has entered the following health concerns:
- Symptoms: {symptoms_text}
- Duration: {duration}
- Stated Severity: {severity}
- Additional Context / History: {additional_info or 'None provided'}

CRITICAL MEDICAL SAFETY RULES:
1. You DO NOT provide a definitive diagnosis or medical prescription.
2. You provide only preliminary educational triage guidance.
3. If symptoms suggest emergency (e.g. crushing chest pain, sudden facial drooping/numbness, severe respiratory distress, acute heavy bleeding), set urgency_level to "emergency".
4. You must select one primary recommended specialization from strictly this list:
   ['General Medicine', 'Cardiology', 'Dermatology', 'Neurology', 'Orthopedics', 'Pediatrics', 'Pulmonology', 'Gastroenterology', 'Endocrinology', 'Psychiatry', 'ENT', 'Ophthalmology', 'Gynecology']

Respond ONLY with a valid JSON object strictly formatted as:
{{
  "possible_concerns": "1-2 sentences summarizing general possible health concern categories (not definitive diagnosis)",
  "recommended_specialization": "Exact matching string from allowed list",
  "urgency_level": "one of: routine, consult_soon, urgent, emergency",
  "guidance_notes": "3-4 bullet points or concise paragraph with helpful self-care, warning signs to watch, and what questions to prepare for the doctor. Mention seeking emergency medical care if symptoms worsen."
}}
"""
                response = model.generate_content(prompt)
                raw_text = response.text.strip()

                # Clean markdown backticks if returned
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                data = json.loads(raw_text)

                # Validate specialization
                spec = data.get("recommended_specialization", "General Medicine")
                if spec not in SPECIALTY_CHOICES:
                    spec = "General Medicine"

                urgency = data.get("urgency_level", "routine").lower()
                if urgency not in ['routine', 'consult_soon', 'urgent', 'emergency']:
                    urgency = 'routine'

                return {
                    'success': True,
                    'source': 'Gemini AI',
                    'possible_concerns': data.get("possible_concerns", "General non-specific symptoms reported."),
                    'recommended_specialization': spec,
                    'urgency_level': urgency,
                    'guidance_notes': data.get("guidance_notes", "Please schedule an appointment with a doctor for full clinical evaluation."),
                    'raw_response': raw_text
                }

        except Exception as e:
            logger.warning(f"Gemini API call failed, invoking clinical rule-based triage: {e}")

    # Clinical Rule-Based Fallback Engine
    return rule_based_symptom_triage(symptoms_text, duration, severity, additional_info)


def chat_with_assistant(message, role='patient'):
    """
    Powers the site-wide AI Assistant chat widget. Answers general health
    questions and helps the user navigate the website. Uses Gemini if a key
    is configured, otherwise falls back to a simple keyword-matched guide so
    the widget never breaks even without an API key.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            model_names = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
            model = None
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    break
                except Exception:
                    continue

            if model:
                prompt = f"""
You are "SmartHealth Assistant", a friendly helper chatbot embedded inside a
hospital management website called SmartHealth in India. The person chatting
with you is logged in as a {role}. Many patients here are more comfortable in
Tanglish (a natural mix of Tamil and English, written in English/Latin
script) than pure English -- respond in warm, natural Tanglish, similar to
how a friendly local hospital receptionist would speak. If the user's own
message is in plain English, you may still reply in simple Tanglish unless
they clearly seem to prefer English.

You have two jobs:
1. Answer general health/wellness questions in simple, safe, non-diagnostic
   language (you are NOT a doctor and must never give a definitive diagnosis
   or prescribe medication -- for anything specific to their own symptoms,
   direct them to use the site's "AI Symptom Assessment" feature or book an
   appointment with a doctor).
2. Help the person navigate the website. Here is the site map you can refer
   them to by name:
   - Patients: Patient Dashboard, Log Health Vitals, Health History, Health
     Trend Analysis, Health Alerts, AI Symptom Assessment, Doctor
     Recommendations, Search Doctors (Doctors Directory), Book Appointment,
     My Appointments, Medical Records, Health Summary Card, Notifications,
     Account & Profile Settings.
   - Doctors: Doctor Dashboard, Appointment Requests, Today's Schedule, All
     Patients / My Patients, Notifications.
   - Admins: Admin Dashboard, Patient Management, Doctor Management,
     Appointment Management, Health Records, Analytics & Reports.

Keep replies SHORT -- 1 to 3 short sentences maximum, warm, and practical.
Brevity matters more than completeness here. If a question is a medical
emergency (e.g. chest pain, difficulty breathing, stroke symptoms), tell them
to seek emergency care immediately instead of chatting further.

User's message: {message}

Reply with plain text only (no markdown headers, no JSON), in Tanglish.
"""
                response = model.generate_content(
                    prompt,
                    generation_config={'max_output_tokens': 150, 'temperature': 0.7}
                )
                reply_text = response.text.strip()
                return {'success': True, 'source': 'Gemini AI', 'reply': reply_text}

        except Exception as e:
            logger.warning(f"Gemini chatbot call failed, using fallback guide: {e}")

    return _chatbot_fallback(message, role)


def _chatbot_fallback(message, role='patient'):
    """Simple keyword-matched navigation/help guide used when no Gemini key is set."""
    m = message.lower()

    nav_map = [
        (['book', 'appointment'], "Appointment book pannanumna: sidebar-la \"Search Doctors\" pogu, doctor-a select pannu, appuram date and available time slot select pannu."),
        (['queue', 'wait'], "Unga live queue position and estimated wait time \"My Appointments\"-la paakalam -- appointment open pannu, Queue Status section check pannu."),
        (['symptom', 'checker', 'diagnos'], "Preliminary AI check-ku, sidebar-la \"AI Symptom Assessment\" use pannu. Adhu specialization and urgency level suggest pannum -- diagnosis illa, so doctor-a follow-up pannunga."),
        (['prescription', 'medicine', 'medical record'], "Unga prescriptions and consultation history \"Medical Records\"-la sidebar-la irukku."),
        (['doctor', 'specialist', 'specialization'], "\"Search Doctors\" / \"Doctors Directory\"-la specialization vachi doctors-a browse and filter pannalam."),
        (['vitals', 'blood pressure', 'sugar', 'heart rate'], "\"Log Health Vitals\"-la unga vitals log pannalam, \"Health Trend Analysis\"-la trends paakalam."),
        (['alert'], "Edhavadhu abnormal vitals irundha, automatic-a \"Health Alerts\"-la varum."),
        (['notification'], "Unga notifications ellam (booking, approval, alert) bell icon illa \"Notifications\" page-la irukku."),
        (['profile', 'password', 'account'], "Unga details \"Account & Profile Settings\"-la update pannalam -- top-right-la unga peru click pannu."),
    ]

    for keywords, reply in nav_map:
        if any(k in m for k in keywords):
            return {'success': True, 'source': 'Guide (no AI key set)', 'reply': reply}

    return {
        'success': True,
        'source': 'Guide (no AI key set)',
        'reply': (
            "AI key set aana apparam, naan health questions-kum site navigation-kum "
            "help pannuven. Ippo, \"appointment book pannradhu eppadi\", \"my medical "
            "records\", \"health alerts\" maari kelu, illana sidebar-a explore pannu. "
            "Unga own symptoms pathi kekkanumna, \"AI Symptom Assessment\" use pannu "
            "illana doctor book pannu."
        )
    }
    """
    Intelligent deterministic clinical triage engine that classifies symptoms
    into appropriate medical specialties and urgency categories.
    """
    combined = f"{symptoms_text} {additional_info}".lower()

    # Red Flag Emergency checks
    emergency_keywords = [
        'crushing chest pain', 'heart attack', 'unconscious', 'paralysis',
        'difficulty breathing', 'severe breathlessness', 'coughing blood',
        'slurred speech', 'facial drooping', 'stroke', 'anaphylaxis',
        'severe head injury', 'sudden blindness'
    ]
    is_emergency = any(k in combined for k in emergency_keywords)

    if is_emergency:
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'High-risk acute physiological symptoms requiring immediate intervention.',
            'recommended_specialization': 'Cardiology' if 'chest' in combined or 'heart' in combined else 'General Medicine',
            'urgency_level': 'emergency',
            'guidance_notes': 'EMERGENCY: These symptoms may indicate an acute life-threatening medical emergency. Please call local emergency medical services immediately or report to the nearest emergency department without delay.',
            'raw_response': 'Generated via deterministic clinical red-flag protocol.'
        }

    # Cardiology
    cardio_keywords = ['chest pain', 'palpitation', 'irregular heartbeat', 'high bp', 'hypertension', 'angina']
    if any(k in combined for k in cardio_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Cardiovascular and hemodynamic irregularities.',
            'recommended_specialization': 'Cardiology',
            'urgency_level': 'urgent' if severity == 'severe' else 'consult_soon',
            'guidance_notes': 'Rest in a comfortable upright position. Avoid strenuous exertion, caffeine, and sudden physical shock. Seek urgent evaluation if pain radiates to the jaw or left arm.',
            'raw_response': 'Rule match: Cardiology'
        }

    # Pulmonology / Respiratory
    pulm_keywords = ['cough', 'shortness of breath', 'wheezing', 'asthma', 'phlegm', 'bronchitis', 'lung', 'chest tightness']
    if any(k in combined for k in pulm_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Upper or lower respiratory tract irritation, infection, or airway obstruction.',
            'recommended_specialization': 'Pulmonology',
            'urgency_level': 'urgent' if severity == 'severe' else 'consult_soon',
            'guidance_notes': 'Maintain good indoor air ventilation. Stay hydrated with warm fluids and note if you develop a high fever or blueness around lips.',
            'raw_response': 'Rule match: Pulmonology'
        }

    # Dermatology
    derm_keywords = ['rash', 'skin', 'itching', 'eczema', 'acne', 'hives', 'mole', 'dermatitis', 'lesion', 'psoriasis']
    if any(k in combined for k in derm_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Dermatological condition, cutaneous allergy, or localized inflammatory response.',
            'recommended_specialization': 'Dermatology',
            'urgency_level': 'routine' if severity != 'severe' else 'consult_soon',
            'guidance_notes': 'Avoid scratching or applying harsh soaps or perfumed ointments. Take photos of the affected area to share during your doctor consultation.',
            'raw_response': 'Rule match: Dermatology'
        }

    # Neurology
    neuro_keywords = ['headache', 'migraine', 'dizziness', 'vertigo', 'numbness', 'tingling', 'tremor', 'seizure', 'memory']
    if any(k in combined for k in neuro_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Neurological, cephalic, or vestibular nervous system disturbance.',
            'recommended_specialization': 'Neurology',
            'urgency_level': 'urgent' if severity == 'severe' else 'consult_soon',
            'guidance_notes': 'Rest in a quiet, darkened room. Track frequency, duration, and any accompanying light sensitivity or nausea.',
            'raw_response': 'Rule match: Neurology'
        }

    # Orthopedics
    ortho_keywords = ['joint pain', 'knee pain', 'back pain', 'bone', 'fracture', 'sprain', 'shoulder pain', 'arthritis', 'spine']
    if any(k in combined for k in ortho_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Musculoskeletal strain, articular inflammation, or structural joint condition.',
            'recommended_specialization': 'Orthopedics',
            'urgency_level': 'consult_soon' if severity in ['moderate', 'severe'] else 'routine',
            'guidance_notes': 'Apply R.I.C.E principles (Rest, Ice, Compression, Elevation) where applicable. Avoid high-impact loads until clinically examined.',
            'raw_response': 'Rule match: Orthopedics'
        }

    # Gastroenterology
    gastro_keywords = ['stomach pain', 'abdominal', 'nausea', 'vomiting', 'diarrhea', 'constipation', 'acidity', 'gas', 'bloating', 'indigestion']
    if any(k in combined for k in gastro_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Gastrointestinal tract inflammation, gastric dysmotility, or food-related intolerance.',
            'recommended_specialization': 'Gastroenterology',
            'urgency_level': 'urgent' if severity == 'severe' else 'consult_soon',
            'guidance_notes': 'Sip oral rehydration salts (ORS) or electrolyte solutions. Stick to a bland diet (bananas, rice, applesauce, toast) and avoid greasy food.',
            'raw_response': 'Rule match: Gastroenterology'
        }

    # Endocrinology
    endo_keywords = ['sugar', 'diabetes', 'thyroid', 'excessive thirst', 'frequent urination', 'sudden weight loss', 'hormone']
    if any(k in combined for k in endo_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Endocrine or metabolic regulation imbalance.',
            'recommended_specialization': 'Endocrinology',
            'urgency_level': 'consult_soon',
            'guidance_notes': 'Log fasting and post-prandial blood sugar readings if you have a glucometer. Keep a 3-day food and water intake diary for your physician.',
            'raw_response': 'Rule match: Endocrinology'
        }

    # ENT
    ent_keywords = ['ear', 'throat', 'sinus', 'hearing', 'tonsil', 'nasal', 'hoarseness', 'runny nose']
    if any(k in combined for k in ent_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Otorhinolaryngological (ear, nose, throat) irritation or upper airway infection.',
            'recommended_specialization': 'ENT',
            'urgency_level': 'routine' if severity != 'severe' else 'consult_soon',
            'guidance_notes': 'Gargle warm salt water for throat irritation. Stay well-hydrated and consider steam inhalation for sinus congestion.',
            'raw_response': 'Rule match: ENT'
        }

    # Psychiatry
    psych_keywords = ['depression', 'anxiety', 'panic', 'stress', 'insomnia', 'sleep disorder', 'mental fatigue']
    if any(k in combined for k in psych_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Psychological well-being, mood regulation, or chronic stress response.',
            'recommended_specialization': 'Psychiatry',
            'urgency_level': 'consult_soon',
            'guidance_notes': 'Practice controlled deep breathing exercises. Confide in a trusted family member or counselor, and maintain a consistent sleep routine.',
            'raw_response': 'Rule match: Psychiatry'
        }

    # Ophthalmology
    eye_keywords = ['eye', 'vision', 'blurred vision', 'red eye', 'eye discharge', 'dry eyes']
    if any(k in combined for k in eye_keywords):
        return {
            'success': True,
            'source': 'Clinical Triage Engine',
            'possible_concerns': 'Ophthalmic surface irritation or visual acuity concerns.',
            'recommended_specialization': 'Ophthalmology',
            'urgency_level': 'consult_soon',
            'guidance_notes': 'Refrain from rubbing eyes. Avoid contact lenses until examined by an eye specialist.',
            'raw_response': 'Rule match: Ophthalmology'
        }

    # Default General Medicine
    urgency_map = {'mild': 'routine', 'moderate': 'consult_soon', 'severe': 'urgent'}
    return {
        'success': True,
        'source': 'Clinical Triage Engine',
        'possible_concerns': 'Systemic or generalized health symptoms requiring initial medical triage.',
        'recommended_specialization': 'General Medicine',
        'urgency_level': urgency_map.get(severity, 'consult_soon'),
        'guidance_notes': 'Monitor your body temperature, stay hydrated, rest adequately, and maintain a record of symptom progression for your consultation.',
        'raw_response': 'General Medicine default triage'
    }


def generate_trend_insight(records_count, avg_hr, avg_sys, avg_dia, avg_sugar, latest_weight, days=30):
    """
    Generates a short natural-language insight about a patient's recent
    vitals trend. Uses Gemini if available, otherwise a simple deterministic
    summary built from the same averages already computed for the page.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    if records_count == 0:
        return {
            'success': True, 'source': 'none',
            'insight': "No health data logged in this period yet -- log your vitals to see trend insights here."
        }

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_names = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
            model = None
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    break
                except Exception:
                    continue

            if model:
                prompt = f"""
You are a cautious health-data summarizer inside a patient dashboard. You are
NOT diagnosing. Based on these {days}-day average vitals from {records_count}
logged entries, write ONE short, plain-language insight (max 2 sentences) a
patient would find useful. Mention any value that looks outside a normal
healthy range and suggest they discuss it with their doctor if so. If
everything looks normal, say that reassuringly.

Average Heart Rate: {avg_hr if avg_hr else 'not logged'} bpm
Average Blood Pressure: {avg_sys if avg_sys else '?'}/{avg_dia if avg_dia else '?'} mmHg
Average Blood Sugar: {avg_sugar if avg_sugar else 'not logged'} mg/dL
Latest Weight: {latest_weight if latest_weight else 'not logged'} kg

Reply with plain text only, no markdown, no JSON.
"""
                response = model.generate_content(prompt)
                return {'success': True, 'source': 'Gemini AI', 'insight': response.text.strip()}
        except Exception as e:
            logger.warning(f"Gemini trend insight call failed, using fallback: {e}")

    return _trend_insight_fallback(avg_hr, avg_sys, avg_dia, avg_sugar)


def _trend_insight_fallback(avg_hr, avg_sys, avg_dia, avg_sugar):
    flags = []
    if avg_hr:
        if avg_hr > 100:
            flags.append("your average heart rate is a bit elevated")
        elif avg_hr < 60:
            flags.append("your average heart rate is a bit low")
    if avg_sys and avg_dia:
        if avg_sys >= 135 or avg_dia >= 88:
            flags.append("your average blood pressure is on the higher side")
    if avg_sugar:
        if avg_sugar >= 140:
            flags.append("your average blood sugar is on the higher side")

    if flags:
        joined = " and ".join(flags)
        return {
            'success': True, 'source': 'Summary (no AI key set)',
            'insight': f"Over this period, {joined} -- consider discussing this with your doctor at your next visit."
        }
    return {
        'success': True, 'source': 'Summary (no AI key set)',
        'insight': "Your logged vitals for this period are within a typical healthy range. Keep up the consistent tracking!"
    }


def generate_admin_summary(total_patients, total_doctors, total_appointments, pending_count, completed_count, active_alerts):
    """
    Generates a short natural-language narrative for the admin analytics
    dashboard. Uses Gemini if available, otherwise a simple deterministic
    summary built from the same stats already computed for the page.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_names = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
            model = None
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    break
                except Exception:
                    continue

            if model:
                prompt = f"""
You are a clinic operations analyst. Based on these current platform stats,
write ONE short, plain-language operational summary (max 2 sentences) for a
hospital administrator's dashboard. Be factual and specific with the numbers
given, and note anything that stands out (e.g. many pending appointments, or
many active health alerts needing attention).

Total Patients: {total_patients}
Total Doctors: {total_doctors}
Total Appointments: {total_appointments}
Pending Appointments: {pending_count}
Completed Appointments: {completed_count}
Active Health Alerts: {active_alerts}

Reply with plain text only, no markdown, no JSON.
"""
                response = model.generate_content(prompt)
                return {'success': True, 'source': 'Gemini AI', 'summary': response.text.strip()}
        except Exception as e:
            logger.warning(f"Gemini admin summary call failed, using fallback: {e}")

    parts = [f"{total_patients} patients and {total_doctors} doctors are registered, with {total_appointments} total appointments."]
    if pending_count > 0:
        parts.append(f"{pending_count} appointment(s) are still pending confirmation.")
    if active_alerts > 0:
        parts.append(f"{active_alerts} active health alert(s) may need attention.")
    return {'success': True, 'source': 'Summary (no AI key set)', 'summary': " ".join(parts)}


def explain_prescription(diagnosis, prescription_text, notes=""):
    """
    Generates a plain-language, patient-friendly explanation of a doctor's
    diagnosis and prescription. Uses Gemini if available, otherwise returns
    a simple framing so the page still works without an AI key.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_names = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
            model = None
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    break
                except Exception:
                    continue

            if model:
                prompt = f"""
You are a patient education assistant. A doctor has written the following
clinical diagnosis and prescription. Rewrite it in simple, warm, everyday
language a patient with no medical background can understand. Explain what
the diagnosis roughly means, what each medicine is generally for, and any
advice given. Do NOT invent new medicines or dosages -- only explain what is
given. Keep it to a short paragraph (4-6 sentences).

Diagnosis: {diagnosis}
Prescription: {prescription_text}
Doctor's Notes: {notes or 'None'}

Reply with plain text only, no markdown, no JSON.
"""
                response = model.generate_content(prompt)
                return {'success': True, 'source': 'Gemini AI', 'explanation': response.text.strip()}
        except Exception as e:
            logger.warning(f"Gemini prescription explanation call failed, using fallback: {e}")

    return {
        'success': True, 'source': 'Guide (no AI key set)',
        'explanation': (
            "A simplified explanation isn't available right now (no AI key configured). "
            "Please review the diagnosis and prescription above, and ask your doctor to "
            "clarify any part you're unsure about."
        )
    }


def calculate_health_risk_score(record):
    """
    Transparent, rule-based Health Risk Score (0-100) computed from a
    HealthRecord's vitals + BMI. This is deliberately NOT purely AI-generated
    -- the score and risk level are deterministic and explainable, per safety
    requirements. Gemini (if configured) is used only to phrase a friendlier
    natural-language explanation of the SAME rule-based result -- it never
    changes the score or risk level itself.

    Returns a dict: score (0-100), risk_level ('low'/'moderate'/'high'),
    flags (list of human-readable reasons points were deducted), explanation.
    """
    score = 100
    flags = []

    hr = record.heart_rate
    if hr:
        if hr > 120 or hr < 45:
            score -= 20; flags.append(f"Heart rate {hr} bpm is significantly outside the normal range (60-100 bpm).")
        elif hr > 100 or hr < 60:
            score -= 10; flags.append(f"Heart rate {hr} bpm is slightly outside the normal range (60-100 bpm).")

    sys_bp, dia_bp = record.systolic_bp, record.diastolic_bp
    if sys_bp and dia_bp:
        if sys_bp >= 140 or dia_bp >= 90:
            score -= 20; flags.append(f"Blood pressure {sys_bp}/{dia_bp} mmHg is in the high range (Stage 2 hypertension territory).")
        elif sys_bp >= 130 or dia_bp >= 80:
            score -= 10; flags.append(f"Blood pressure {sys_bp}/{dia_bp} mmHg is elevated (Stage 1 hypertension territory).")

    spo2 = record.oxygen_saturation
    if spo2:
        if spo2 < 90:
            score -= 25; flags.append(f"SpO2 {spo2}% is critically low -- oxygenation may be inadequate.")
        elif spo2 < 95:
            score -= 12; flags.append(f"SpO2 {spo2}% is below the healthy range (95%+).")

    temp = float(record.temperature) if record.temperature else None
    if temp:
        if temp >= 102:
            score -= 15; flags.append(f"Temperature {temp}\u00b0F indicates a high fever.")
        elif temp >= 100.4:
            score -= 8; flags.append(f"Temperature {temp}\u00b0F indicates a mild fever.")

    sugar = float(record.blood_sugar) if record.blood_sugar else None
    if sugar:
        if sugar >= 180 or sugar < 60:
            score -= 15; flags.append(f"Blood sugar {sugar} mg/dL is significantly outside a healthy range.")
        elif sugar >= 126 or sugar < 70:
            score -= 8; flags.append(f"Blood sugar {sugar} mg/dL is outside the typical healthy range.")

    bmi = record.calculate_bmi()
    if bmi:
        if bmi >= 30 or bmi < 16:
            score -= 10; flags.append(f"BMI {bmi} indicates obesity or significant underweight.")
        elif bmi >= 25 or bmi < 18.5:
            score -= 5; flags.append(f"BMI {bmi} is outside the typical healthy range (18.5-24.9).")

    score = max(0, min(100, score))

    if score >= 80:
        risk_level = 'low'
    elif score >= 50:
        risk_level = 'moderate'
    else:
        risk_level = 'high'

    explanation = _generate_risk_explanation(score, risk_level, flags)

    return {
        'score': score,
        'risk_level': risk_level,
        'flags': flags,
        'explanation': explanation,
    }


def _generate_risk_explanation(score, risk_level, flags):
    """Natural-language explanation of the ALREADY-COMPUTED rule-based score. Gemini only rephrases; it cannot change the score/level."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_names = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
            model = None
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    break
                except Exception:
                    continue
            if model:
                flags_text = "; ".join(flags) if flags else "No vitals were outside the typical healthy range."
                prompt = f"""
A rule-based health scoring system has ALREADY calculated the following
result for a patient. Do NOT change the score or risk level -- only explain
it warmly and simply in 2-3 sentences, and give one or two general,
non-prescriptive lifestyle suggestions if relevant (e.g. "consider discussing
this with your doctor", general diet/rest advice). Never mention specific
medications or dosages.

Score: {score}/100
Risk Level: {risk_level.upper()}
Findings: {flags_text}

Reply with plain text only.
"""
                response = model.generate_content(prompt, generation_config={'max_output_tokens': 150})
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini risk explanation call failed, using fallback: {e}")

    if not flags:
        return "All the vitals you logged fall within typical healthy ranges. Keep up the consistent tracking and healthy habits!"
    return "Based on your latest vitals: " + " ".join(flags) + " Consider discussing these readings with your doctor, especially if they persist."
