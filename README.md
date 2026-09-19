# Smart Health Monitoring and Appointment System

An enterprise-grade, full-stack healthcare web application combining continuous patient vital telemetry, automated clinical alerts, Google Gemini AI-powered preliminary symptom triage, specialist recommendations, live estimated waiting room queue predictions, and electronic medical records/prescriptions.

---

## 🌟 Key Features

### 1. 🤖 AI Symptom Assessment & Triage
- **Guided Multi-Step Wizard**: Select symptoms via interactive chips, specify onset duration, indicate severity level, and provide clinical context.
- **Powered by Google Gemini**: Backed by `google-generativeai` with strict medical safety guardrails (identifies concern categories, assesses urgency, recommends clinical specialties, and emphasizes emergency care for acute symptoms).
- **Graceful Deterministic Fallback Engine**: If no API key is provided or the network is offline, an intelligent clinical rule engine categorizes symptoms and computes urgency without interruption.
- **Direct Specialist Match**: Matches triage output directly to certified doctors with 1-click booking.

### 2. 📊 Personal Health Monitoring & Trend Analytics
- **Vital Telemetry Logging**: Record Heart Rate (Pulse), Blood Pressure (Systolic/Diastolic), Blood Glucose, SpO2 (Oxygen Saturation), Weight, Height, and Temperature.
- **Dynamic Trend Graphs**: Multi-metric interactive charts powered by **Chart.js** with 7-Day, 30-Day, and 3-Month period filters.
- **Automated Clinical Health Alerts**: Immediate threshold monitoring for Stage 2 hypertension, tachycardia/bradycardia, hyperglycemia, and hypoxia with automated notifications.

### 3. ⏱️ Smart Clinic Queue & Waiting-Time Prediction
- **Dynamic Real-Time Queue Tracker**: Displays the patient's queue position, count of preceding patients, and algorithmic estimated waiting time (`Preceding Patients × Doctor Slot Duration`).
- **Live Background Polling**: Real-time status synchronization without requiring manual page reloads.
- **Transparent Disclaimer**: Clear notifications that wait times are mathematical estimates based on average consultation pace.

### 4. 📅 Robust Appointment & Scheduling System
- **Dynamic Slot Availability**: Generates valid time slots according to doctor consultation hours and slot durations.
- **Double-Booking Prevention**: Automatically disables conflicting or already-reserved slots.
- **Past-Date Safeguards**: Prevents scheduling appointments in the past.
- **Full Booking Lifecycle**: Pending &rarr; Approved &rarr; In Consultation &rarr; Completed &rarr; Cancelled/Rejected.

### 5. 💊 Electronic Prescriptions & Medical Records
- **Standardized Medical Sheets**: Professional prescription output formatted with clinic headers, patient demographics, clinical diagnosis, Rx itemization (medication, dose, frequency, duration, instructions), and physician signature lines.
- **One-Click Print to PDF**: Print-optimized CSS rules for patients and doctors.

### 6. 👥 Role-Based Portals & Strict Access Control
- **Patient Portal**: Daily telemetry, alerts, AI triage wizard, queue tracker, my appointments, prescription archives.
- **Doctor Portal**: Daily schedule, queue management, incoming request approvals/rejections with custom notes, patient medical history lookup, and consultation note/prescription generator.
- **Admin Portal**: Platform metrics, appointment status distribution chart, doctor specialization capacity chart, doctor verification/approval toggles, and patient management.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+, Django 6.0+
- **Database**: SQLite
- **AI Integration**: Google Gemini API (`google-generativeai`) + Clinical Rule-Based Fallback Engine
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4, Vanilla JavaScript
- **Design Tokens**:
  - Primary Teal: `#0F766E`
  - Secondary Blue: `#2563EB`
  - Background: `#F8FAFC`
  - Cards: `#FFFFFF`
  - Text: `#0F172A` / Muted: `#64748B`

---

## 📂 Project Structure

```
smart healthMonitoring system/
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── README.md
├── health_system/              # Central project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                   # Authentication, User model, Profiles & RBAC
│   ├── models.py               # Custom User (patient/doctor/admin), Profiles
│   ├── views.py                # Login, registration, profile, notifications
│   ├── forms.py                # User & profile forms
│   ├── urls.py
│   ├── decorators.py           # @patient_required, @doctor_required, @admin_required
│   ├── context_processors.py   # Global notifications & role context
│   └── management/commands/
│       └── seed_data.py        # Demo dataset generator
├── health/                     # Vitals, alerts, AI triage, trends
│   ├── models.py               # HealthRecord, HealthAlert, SymptomAssessment
│   ├── views.py                # Telemetry entry, trends, alerts, AI wizard
│   ├── forms.py                # Vitals & symptom forms
│   ├── gemini_service.py       # Gemini API caller & clinical fallback engine
│   ├── urls.py
│   └── tests.py
├── appointments/               # Bookings, queue tracker, prescriptions
│   ├── models.py               # Appointment, ConsultationRecord, Notification
│   ├── views.py                # Directory, booking, slots API, queue API, records
│   ├── forms.py                # Booking & consultation forms
│   ├── urls.py
│   └── tests.py
├── dashboard/                  # Multi-role portals
│   ├── views.py                # Home, Patient Dashboard, Doctor Dashboard, Admin Dashboard
│   └── urls.py
├── templates/                  # Bootstrap 5 layouts and views
│   ├── base.html
│   ├── home.html
│   ├── components/             # navbar, sidebar, alerts, footer
│   ├── accounts/               # login, patient_register, doctor_register, profile
│   ├── patient/                # dashboard, health_entry, history, trends, queue, records
│   ├── health/                 # symptom_assessment, assessment_result, recommendations
│   ├── appointments/           # doctor_list, doctor_profile, book, confirmation
│   ├── doctor/                 # dashboard, requests, today_appointments, patients, consult
│   ├── admin_portal/           # dashboard, patients, doctors, appointments, reports
│   └── notifications/          # list.html
└── static/
    ├── css/custom.css          # Healthcare UI design tokens & responsive sidebar
    └── js/
        ├── main.js             # Symptom chips, slot loader, queue live polling
        └── charts.js           # Chart.js trend & analytics charts
```

---

## 🚀 Getting Started

### Option A: Running from Extracted ZIP (Quickstart for Peers)
1. **Unzip** the archive into a folder of your choice.
2. Open a terminal in the project directory.
3. **(Recommended) Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (Command Prompt / PowerShell):
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```
4. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Set up local environment configuration:**
   Copy `.env.example` to `.env`:
   ```bash
   # Windows:
   copy .env.example .env
   # macOS / Linux:
   cp .env.example .env
   ```
6. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```
7. **Populate initial demonstration accounts & data:**
   ```bash
   python manage.py seed_data
   ```
8. **Start the local server:**
   ```bash
   python manage.py runserver
   ```
   Visit **`http://127.0.0.1:8000`** in your web browser.

---

### Option B: Deploying to Render (Live Cloud Hosting)
This project includes pre-configured Render deployment manifests (`build.sh`, `Procfile`, and `render.yaml`).

1. **Push your code to GitHub** (see GitHub steps below).
2. Go to **[Render Dashboard](https://dashboard.render.com/)** and click **New +** &rarr; **Web Service**.
3. Connect your GitHub repository.
4. Render will auto-detect settings or you can configure:
   - **Environment:** `Python 3`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn health_system.wsgi:application`
5. **Add Environment Variables in Render:**
   - `SECRET_KEY`: *(Generate a secure random string or use Render's generate button)*
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.onrender.com`
   - `GEMINI_API_KEY`: *(Optional: Your Google Gemini API key for live AI triage)*
   - `DATABASE_URL`: *(Optional: If using Render PostgreSQL, paste the Internal Database URL)*
6. Click **Deploy Web Service**. Render runs `./build.sh` (which installs packages, collects static files, runs migrations, and seeds demonstration accounts).
7. Your app is live at `https://<your-app-name>.onrender.com`!

---

### Option C: Uploading to GitHub
1. Initialize git in the workspace:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Smart Health Monitoring System with Render deployment config"
   ```
2. Create a new repository on GitHub (e.g. `smart-health-monitoring-system`).
3. Link and push to GitHub:
   ```bash
   git remote add origin https://github.com/<your-username>/smart-health-monitoring-system.git
   git branch -M main
   git push -u origin main
   ```

---

## 🚪 Dedicated Login Portals & Demo Accounts

| Portal | Dedicated URL | Allowed Roles | Default Demo Username | Demo Password | Purpose |
|---|---|---|---|---|---|
| **Patient Portal** | `/accounts/login/` *(or `/accounts/patient/login/`)* | Patient (`role='patient'`) | `patient1` *(or `patient2`)* | `patient123` | Patient dashboard, vitals, AI triage wizard, queue tracker, Rx |
| **Doctor Portal** | `/accounts/doctor/login/` | Doctor (`role='doctor'`) | `dr_sarah` *(Cardiology)*, `dr_chen` *(Gen Med)* | `doctor123` | Queue schedule, approve/reject requests, write consultations & Rx |
| **Admin Console** | `/accounts/admin/login/` | Admin (`is_staff`/`is_superuser`) | `admin` | `admin123` | System oversight, doctor accreditation, telemetry records |

*(Note: All login forms support logging in with **either Username OR Email**).*

---

## 🧪 Running Automated Tests

Run the complete test suite across all Django apps:
```bash
python manage.py test
```
Run the system health check:
```bash
python manage.py check
```

