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


_TANGLISH_WORDS = {
    'enna', 'eppadi', 'epdi', 'irukku', 'irukkum', 'iruku', 'panna', 'pannanum', 'pannalam',
    'pannu', 'pannunga', 'panren', 'solu', 'sollu', 'solunga', 'venum', 'venam', 'vandha',
    'vali', 'kudu', 'kudunga', 'paaru', 'paarunga', 'irundha', 'irundhaa', 'edhu', 'enga',
    'naal', 'romba', 'konjam', 'illa', 'illai', 'nalla', 'udambu', 'thanni', 'saapda',
    'saapdanum', 'vayiru', 'thalai', 'sali', 'irumal', 'kaichal', 'jwaram', 'mookku',
    'enakku', 'unga', 'naan', 'nee', 'ennoda', 'eppo', 'aagum', 'aaguthu', 'seri', 'sari',
    'podu', 'poda', 'vaanga', 'ketu', 'kelu', 'theriyum', 'theriyala', 'puriyala', 'vandhuchu',
}


def _looks_tanglish(message):
    """True if the message is Tanglish (Tamil written in English letters) or Tamil script."""
    import re
    if re.search(r'[\u0B80-\u0BFF]', message or ''):
        return True
    words = set(re.findall(r"[a-z]+", (message or '').lower()))
    return bool(words & _TANGLISH_WORDS)


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
                reply_language = 'Tanglish' if _looks_tanglish(message) else 'English'
                prompt = f"""
You are "SmartHealth Assistant", a friendly helper chatbot embedded inside a
hospital management website called SmartHealth in India. The person chatting
with you is logged in as a {role}. LANGUAGE RULE: reply in the same language
style the user wrote in. The user's message is detected as {reply_language}.
If it is English, reply in simple, clear English only (no Tamil words). If it
is Tanglish (Tamil written in English letters), reply in warm, natural
Tanglish like a friendly local hospital receptionist.

You have two jobs:
1. Answer general health/wellness questions DIRECTLY and helpfully in simple,
   safe language. When someone asks about home remedies or self-care for a
   common, mild problem (fever, cold, cough, headache, acidity, body pain,
   stomach upset, sore throat, etc.), actually give 3 to 4 practical tips
   (rest, fluids, warm water, light food, steam, etc.) -- do NOT just tell
   them to use the symptom checker or book a doctor. If the person says they
   don't know the cause or what to do, still give the general care tips first.
   Never give a definitive diagnosis and never name medicines or doses. After
   the tips, add ONE short line on when to see a doctor (for example fever
   lasting more than 2 to 3 days, very high fever, breathing trouble, or
   symptoms getting worse), and you may mention the site's "AI Symptom
   Assessment" or "Book Appointment" as an extra option, not as the whole answer.
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

Keep replies short and easy to read -- at most 4 to 5 short sentences, warm and
practical. If a question is a medical
emergency (e.g. chest pain, difficulty breathing, stroke symptoms), tell them
to seek emergency care immediately instead of chatting further.

User's message: {message}

Reply with plain text only (no markdown headers, no JSON), in {reply_language}.
"""
                response = model.generate_content(
                    prompt,
                    generation_config={'max_output_tokens': 350, 'temperature': 0.7}
                )
                reply_text = response.text.strip()
                return {'success': True, 'source': 'Gemini AI', 'reply': reply_text}

        except Exception as e:
            logger.warning(f"Gemini chatbot call failed, using fallback guide: {e}")

    return _chatbot_fallback(message, role)


def _chatbot_fallback(message, role='patient'):
    """Simple keyword-matched navigation/help guide used when no Gemini key is set."""
    m = message.lower()

    if not _looks_tanglish(message):
        return _chatbot_fallback_english(m)

    remedies = [
        (['fever', 'kaichal', 'jwaram', 'temperature'],
         "Fever irundha nalla rest edunga, niraya thanni / ORS / kanji kudunga, light-a saapdunga, thin cotton dress podunga. Neththila eera thuni vachchu, udambu thudachu vidalam. Fever 2-3 naal-ku mela irundha, romba adhigama irundha, illa breathing problem irundha doctor-a paarunga."),
        (['cold', 'sali', 'runny nose', 'sneez'],
         "Sali irundha vennir niraya kudunga, steam pidinga, uppu thanni-la gargle pannunga, nalla rest edunga. 5-7 naal-ku mela irundha illa fever sethu irundha doctor-a paarunga."),
        (['cough', 'irumal', 'sore throat', 'throat'],
         "Irumal / throat pain-ku sudu thanni, uppu thanni gargle, thaen-la konjam inji sethu saapdalam (1 vayasu-ku keezha kuzhandhaiku thaen venaam). Thanni niraya kudunga, thoosi / pugai thavirunga. 1 vaaram-ku mela irundha doctor-a paarunga."),
        (['headache', 'thalai vali', 'head pain', 'migraine'],
         "Thalai vali-ku amaidhiyana, irutta idathula rest edunga, niraya thanni kudunga, neram-ku saapdunga, nenjukku mela screen paakama irukunga. Romba severe-a irundha illa thirumba thirumba vandha doctor-a paarunga."),
        (['acidity', 'gas', 'stomach', 'vayiru', 'indigestion', 'vomit', 'diarrh'],
         "Vayiru prachanai-ku spicy / oily food thavirunga, konjam konjam-a thanni / ORS kudunga, light-a kanji / curd rice saapdunga. Thirumba thirumba vomit, rathathoda motion, illa romba weakness irundha udane doctor-a paarunga."),
        (['body pain', 'udambu vali', 'back pain', 'muscle', 'joint'],
         "Udambu vali-ku nalla rest edunga, sudu thanni othadam kodunga, light-a stretch pannunga, niraya thanni kudunga. Vali romba adhigama irundha illa neenda naal irundha doctor-a paarunga."),
    ]
    wants_nav = any(k in m for k in ['book', 'appointment'])
    if not wants_nav:
        for keywords, reply in remedies:
            if any(k in m for k in keywords):
                return {'success': True, 'source': 'Guide (no AI key set)', 'reply': reply}

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


def _chatbot_fallback_english(m):
    """English version of the keyword fallback guide (used when no AI reply is available)."""
    remedies = [
        (['fever', 'temperature'],
         "For a fever, rest well, drink plenty of water, ORS or coconut water, eat light food like porridge, and wear thin cotton clothes. A damp cloth on the forehead can help. See a doctor if the fever lasts more than 2-3 days, is very high, or you have trouble breathing."),
        (['cold', 'runny nose', 'sneez', 'blocked nose'],
         "For a cold, drink warm fluids, inhale steam, gargle with warm salt water and rest well. See a doctor if it lasts more than 5-7 days or you get a fever."),
        (['cough', 'sore throat', 'throat'],
         "For a cough or sore throat, sip warm water, gargle with warm salt water and avoid dust and smoke. Honey with ginger can soothe the throat (not for children under 1 year). See a doctor if it lasts more than a week."),
        (['headache', 'migraine', 'head pain'],
         "For a headache, rest in a quiet, dark room, drink plenty of water, eat on time and limit screen use. See a doctor if it is severe or keeps coming back."),
        (['acidity', 'gas', 'stomach', 'indigestion', 'vomit', 'diarrh'],
         "For stomach trouble, avoid spicy and oily food, sip water or ORS in small amounts and eat light food like curd rice. See a doctor quickly if vomiting keeps repeating, there is blood in the stool, or you feel very weak."),
        (['body pain', 'back pain', 'muscle', 'joint', 'hand', 'leg pain'],
         "For body or muscle pain, rest, apply a warm compress, do gentle stretching and drink enough water. See a doctor if the pain is severe or lasts many days."),
        (['dehydrat'],
         "Dehydration can cause thirst, dry mouth, dizziness, tiredness and dark urine. Drink water, ORS or coconut water in small sips. If you feel very dizzy or cannot keep fluids down, see a doctor."),
        (['diabet', 'sugar'],
         "For people with diabetes, choose whole grains, vegetables and protein, and cut down on sweets, sugary drinks and white rice portions. Check your sugar regularly and follow your doctor's advice."),
        (['weight', 'lose weight'],
         "To lose weight safely, eat balanced home-cooked meals, avoid sugary and fried food, walk or exercise daily and sleep well. A doctor can give a plan that suits you."),
        (['stress', 'anxiety'],
         "To reduce stress, try deep breathing, a short daily walk, enough sleep and talking to someone you trust. If it feels overwhelming, please talk to a doctor or counsellor."),
        (['chest pain', 'breathing', 'breathless', 'unconscious', 'stroke'],
         "This could be serious. Please get emergency medical help right now or go to the nearest hospital. Do not wait."),
    ]
    wants_nav = any(k in m for k in ['book', 'appointment'])
    if not wants_nav:
        for keywords, reply in remedies:
            if any(k in m for k in keywords):
                return {'success': True, 'source': 'Guide (no AI key set)', 'reply': reply}

    nav_map = [
        (['book', 'appointment'], "To book an appointment: open Doctors Directory, pick a doctor, then choose a date and an available time slot and confirm."),
        (['queue', 'wait'], "You can see your live queue position and estimated wait in My Appointments."),
        (['symptom', 'checker', 'diagnos'], "Use AI Symptom Assessment from the sidebar for a preliminary check. It is not a diagnosis, so please follow up with a doctor."),
        (['prescription', 'medicine', 'medical record'], "Your prescriptions and consultation history are in Medical Records in the sidebar."),
        (['doctor', 'specialist', 'specialization'], "Use Doctors Directory to browse and filter doctors by specialization."),
        (['trend', 'vitals', 'blood pressure', 'heart rate'], "Log your vitals in Log Health Vitals, and see your trends in Health Trend Analysis."),
        (['alert'], "Abnormal vitals automatically appear in Health Alerts."),
        (['notification'], "Your notifications (bookings, approvals, alerts) are under the bell icon or the Notifications page."),
        (['sos', 'emergency'], "The red Emergency SOS button on your dashboard sends an alert to doctors and admins. For a real emergency, please also call your local emergency number."),
        (['profile', 'password', 'account'], "You can update your details in Account Settings: click your name at the top right."),
    ]
    for keywords, reply in nav_map:
        if any(k in m for k in keywords):
            return {'success': True, 'source': 'Guide (no AI key set)', 'reply': reply}

    return {
        'success': True,
        'source': 'Guide (no AI key set)',
        'reply': "I can help with general health questions and with using this site. Try asking about a fever, headache or cold, or how to book an appointment. For your own symptoms, please use AI Symptom Assessment or book a doctor."
    }


def rule_based_symptom_triage(symptoms_text, duration, severity, additional_info=""):
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
