import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)  # Enables frontend fetch access across ports and local networks

# Database configuration: Adjust user/password as needed
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hkbhalar786',  # <-- REPLACE WITH YOUR REAL MYSQL PASSWORD
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

        # 3. Multimodal heuristic AI logic (Static EHR + Continuous Telemetry)
        score = 92
        status = "Optimal"
        alert = "Vitals are within your target range. Keep up regular physical activity."
        prediction = "Recovery metrics align with normal baselines."

        sleep = float(wearable['sleep_hours'])
        baseline = (user['clinical_baseline'] or '').lower()
        hr = wearable['avg_heart_rate']

        if sleep < 6.0:
            score -= 18
            if "asthma" in baseline:
                status = "Warning"
                prediction = "Elevated fatigue detected. Asthma risk slightly increased due to poor sleep recovery."
                alert = "Take a 20-minute rest. Prioritize 7+ hours of sleep tonight."
            else:
                status = "Warning"
                prediction = "Fatigue markers elevated due to insufficient sleep duration."
                alert = "Schedule active recovery. Avoid heavy cardio this evening."

        if hr > 95:
            score -= 15
            status = "Critical" if status == "Warning" else "Warning"
            prediction += " Elevated resting heart rate pattern detected."
            alert = "Elevated resting heart rate detected. Rest and re-check in 15 minutes."

        cursor.close()
        conn.close()

        return jsonify({
            'user': user,
            'smartwatch_live': {
                'steps_today': wearable['steps'],
                'sleep_hours_last_night': float(wearable['sleep_hours']),
                'heart_rate_avg': wearable['avg_heart_rate']
            },
            'ai_analysis': {
                'health_score': max(score, 10),
                'status': status,
                'prediction': prediction,
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