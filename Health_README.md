#  PulseAI: Multimodal Telemetry & Digital Twin Diagnostics

**PulseAI** is a full-stack clinical intelligence platform that fuses real-time wearable telemetry with a **Physics-Informed Machine Learning Digital Twin**. It predicts 30-minute blood glucose trajectories for diabetic patients by combining a Random Forest model (trained on synthetic SimGlucose data) with biological pharmacokinetic/pharmacodynamic (PK/PD) constraints.

---

##  Architecture & Tech Stack
- **Frontend:** Vanilla JS, HTML5, CSS3 (Responsive Clinical Dashboard)
- **Backend:** Python, Flask, REST API
- **Database:** MySQL (User EHR & Wearable Logs)
- **Machine Learning:** Scikit-Learn (Random Forest Regressor), SimGlucose (Digital Twin Simulator)
- **Core Innovation:** Physics-Informed ML (Fuses AI predictions with biological insulin/carb constants to prevent impossible physiological outputs).

---

##  Key Features
1. **Digital Twin Data Generation:** Uses the `simglucose` environment to simulate 10 days of continuous CGM (Continuous Glucose Monitor) metabolic data.
2. **Custom ML Pipeline:** Trains a Random Forest model to forecast 30-min glucose levels based on CGM, Carbs, Insulin, and Heart Rate.
3. **Physics-Informed Inference:** The Flask API intercepts the ML prediction and applies PK/PD biological rules (e.g., *1g Carbs = +2.5 mg/dL, 1U Insulin = -40 mg/dL*) to guarantee clinical safety.
4. **Clinical Portal:** Secure session handling, patient EHR baselines, and live smartwatch telemetry integration.
5. **Live Intervention Simulator:** Frontend dashboard allows doctors to simulate meal/insulin bolus and watch the AI recalculate the trajectory in real-time.

---

##  Project Structure
```text
├── app.py                              # Flask Backend, API Routing & Physics-Informed ML Logic
├── generate_data.py                    # SimGlucose Digital Twin Data Generator
├── train_model.py                      # ML Model Training Pipeline (Random Forest)
├── digital_twin_synthetic_dataset.csv  # Generated 10-day metabolic training data
├── auth.html                           # Frontend Authentication UI
├── auth.css                            # Auth Module Styling (Dark Clinical Theme)
├── authori.js                          # Auth Logic (Fetch API, Tab Switching, Form Validation)
├── index.html                          # Frontend Dashboard UI (Vitals & AI Predictions)
├── index.css                           # Dashboard Styling & Dynamic Status Modifiers
└── README.md