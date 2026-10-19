import os
import joblib
import pandas as pd
import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)  # Enables frontend fetch access across ports and local networks

# ----------------- AI MODEL INITIALIZATION -----------------
# Load the Phase 2 Digital Twin model when the server starts
try:
    model = joblib.load('digital_twin_model.pkl')
    # model_features.pkl is no longer needed since we have a fixed 4-column dataset!
    ML_ENABLED = True
    print("SUCCESS: Digital Twin AI Model Loaded successfully.")
except FileNotFoundError:
    ML_ENABLED = False
    print("WARNING: digital_twin_model.pkl not found. Falling back to basic logic.")

# Database configuration: Adjust user/password as needed
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hkbhalar786',  # <-- Keep your real password here
    'database': 'ai_health_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ----------------- AUTHENTICATION -----------------

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    age = data.get('age', 25)
    gender = data.get('gender', 'Other')
    clinical_baseline = data.get('clinical_baseline', 'None')
    device_model = data.get('device_model', 'Simulator')

    if not email or not password or not full_name:
        return jsonify({'error': 'Full name, email, and password are required'}), 400

    hashed_pw = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO users (full_name, email, password_hash, age, gender, clinical_baseline, device_model)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (full_name, email, hashed_pw, age, gender, clinical_baseline, device_model))
        user_id = cursor.lastrowid

        # Insert an initial smartwatch vitals baseline
        cursor.execute(
            "INSERT INTO wearable_logs (user_id, steps, sleep_hours, avg_heart_rate) VALUES (%s, %s, %s, %s)",
            (user_id, 4500, 6.5, 74)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({'error': 'An account with this email already exists'}), 409
        return jsonify({'error': str(err)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'name': user['full_name'],
                    'email': user['email'],
                    'age': user['age'],
                    'gender': user['gender'],
                    'clinical_baseline': user['clinical_baseline'],
                    'device_model': user['device_model']
                }
            }), 200
        return jsonify({'error': 'Invalid email or password'}), 401
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

# ----------------- DASHBOARD & TELEMETRY -----------------

@app.route('/api/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch user EHR baseline
        cursor.execute("SELECT id, full_name, age, gender, clinical_baseline, device_model FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # 2. Fetch latest wearable logs
        cursor.execute(
            "SELECT steps, sleep_hours, avg_heart_rate, recorded_at FROM wearable_logs WHERE user_id = %s ORDER BY recorded_at DESC LIMIT 1",
            (user_id,)
        )
        wearable = cursor.fetchone() or {'steps': 0, 'sleep_hours': 0.0, 'avg_heart_rate': 72}
        cursor.close()
        conn.close()

        # 3. DIGITAL TWIN AI PREDICTION LOGIC
        if ML_ENABLED:
            clinical_notes = (user['clinical_baseline'] or '').lower()
            current_glucose = 165.0 if 'diabetes' in clinical_notes else 110.0

            # Intercept live intervention triggers from the frontend dashboard
            carbs = float(request.args.get('carbs', 0.0))
            insulin = float(request.args.get('insulin', 0.0))

            # 1. Base Machine Learning Prediction (The AI's guess)
            input_data = {
                'CGM': [current_glucose],
                'Carbs': [carbs],
                'Insulin': [insulin],
                'HeartRate': [wearable['avg_heart_rate']]
            }
            df = pd.DataFrame(input_data) 
            base_prediction = model.predict(df)[0]

            # 2. PHYSICS-INFORMED GUARDRAILS (The Medical Math)
            # 1g Carbs raises glucose by ~2.5 mg/dL | 1 Unit Insulin drops it by ~40 mg/dL
            physio_shift = (carbs * 2.5) - (insulin * 40.0)
            
            # Final Fused Prediction
            predicted_glucose = max(40.0, base_prediction + physio_shift)

            # Route clinical alerts to frontend UI
            prediction_text = f"30-Min Blood Sugar Forecast: {predicted_glucose:.1f} mg/dL (Current: {current_glucose:.1f})"
            
            if predicted_glucose > 180.0:
                status = "Critical"
                alert = "[ HYPERGLYCEMIA RISK ] - Administer insulin or monitor closely."
                score = max(10, 100 - int(predicted_glucose - 180))
            elif predicted_glucose < 70.0:
                status = "Critical"
                alert = "[ HYPOGLYCEMIA RISK ] - Patient requires fast-acting carbohydrates."
                score = max(10, int(predicted_glucose)) 
            elif predicted_glucose > 140.0:
                status = "Warning"
                alert = "Glucose trending elevated. Watch diet and consider light activity."
                score = 82
            else:
                status = "Optimal"
                alert = "Patient is stable. Future trajectory is in the safe zone."
                score = 96

        else:
            # Fallback basic logic if .pkl files are missing
            score = 92
            status = "Optimal"
            prediction_text = "Standard Telemetry Baseline (AI Offline)"
            alert = "Vitals are within range."
            if wearable['avg_heart_rate'] > 95:
                status = "Warning"
                alert = "Elevated resting heart rate detected."
                score = 75

        # Return payload perfectly matching index.html expectation
        return jsonify({
            'user': user,
            'smartwatch_live': {
                'steps_today': wearable['steps'],
                'sleep_hours_last_night': float(wearable['sleep_hours']),
                'heart_rate_avg': wearable['avg_heart_rate']
            },
            'ai_analysis': {
                'health_score': score,
                'status': status,
                'prediction': prediction_text,
                'alert': alert
            }
        }), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/telemetry/log', methods=['POST'])
def log_telemetry():
    """Allows simulated or device streams to insert fresh readings"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    steps = data.get('steps', 0)
    sleep_hours = data.get('sleep_hours', 0.0)
    avg_heart_rate = data.get('avg_heart_rate', 70)

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO wearable_logs (user_id, steps, sleep_hours, avg_heart_rate)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, steps, sleep_hours, avg_heart_rate))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Wearable log recorded'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)