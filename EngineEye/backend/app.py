# app.py - Complete EngineEye Backend (No Duplicates)
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import jwt
import bcrypt
import datetime
import os
from functools import wraps
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"])
app.config['SECRET_KEY'] = 'engineeye_secret_key_2024'



# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
# Initialize Twilio client
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    twilio_enabled = True
    print("✅ Twilio initialized successfully")
    print(f"   Phone number: {TWILIO_PHONE_NUMBER}")
except Exception as e:
    twilio_enabled = False
    print(f"⚠️ Twilio not available: {e}")

def get_db():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Database error: {e}")
        return None

# AI Engine Health Predictor
def predict_engine_health(data):
    health_score = 100.0
    detected_issues = []
    
    # Temperature analysis
    temp = data.get('engine_temp', 90)
    if temp > 115:
        health_score -= 30
        detected_issues.append('Severe Overheating - Immediate Danger')
    elif temp > 105:
        health_score -= 20
        detected_issues.append('High Engine Temperature - Risk of Damage')
    elif temp > 100:
        health_score -= 10
        detected_issues.append('Elevated Temperature - Monitor Closely')
    elif temp < 70:
        health_score -= 5
        detected_issues.append('Engine Too Cold - Allow to Warm Up')
    
    # RPM analysis
    rpm = data.get('rpm', 2000)
    if rpm > 9500:
        health_score -= 25
        detected_issues.append('Critical Over-revving - Engine Damage Risk')
    elif rpm > 8000:
        health_score -= 15
        detected_issues.append('High RPM - Reduce Speed Immediately')
    elif rpm > 7000:
        health_score -= 8
        detected_issues.append('Elevated RPM - Consider Shifting Up')
    
    # Vibration analysis
    vibration = data.get('vibration', 1.0)
    if vibration > 5.0:
        health_score -= 20
        detected_issues.append('Severe Vibrations - Mechanical Issue Detected')
    elif vibration > 3.5:
        health_score -= 12
        detected_issues.append('Unusual Vibrations - Check Engine Mounts')
    elif vibration > 2.5:
        health_score -= 5
        detected_issues.append('Minor Vibrations - Monitor')
    
    # Fuel mixture (Oxygen sensor)
    oxygen = data.get('oxygen_sensor', 0.45)
    if oxygen < 0.2 or oxygen > 0.8:
        health_score -= 15
        detected_issues.append('Fuel Mixture Issue - Check Fuel System')
    elif oxygen < 0.3 or oxygen > 0.7:
        health_score -= 8
        detected_issues.append('Suboptimal Fuel Mixture - Reduce Fuel Consumption')
    
    # Knock detection
    knock = data.get('knock_sensor', 0.1)
    if knock > 0.9:
        health_score -= 25
        detected_issues.append('Severe Engine Knocking - Stop Vehicle')
    elif knock > 0.6:
        health_score -= 15
        detected_issues.append('Engine Knocking Detected - Check Fuel Quality')
    elif knock > 0.4:
        health_score -= 8
        detected_issues.append('Minor Knocking - Use Higher Octane Fuel')
    
    health_score = max(0, min(100, health_score))
    
    # Generate recommendation
    if health_score >= 85:
        recommendation = '✅ Engine is in excellent condition. Continue regular maintenance every 3000 km.'
    elif health_score >= 70:
        recommendation = '⚠️ Engine is in good condition. Schedule routine checkup within next 500 km.'
    elif health_score >= 55:
        recommendation = '🔧 Service recommended. Some parameters are outside optimal range.'
    elif health_score >= 40:
        recommendation = '⚠️⚠️ Immediate service required. Do not ignore warning signs.'
    else:
        recommendation = '🚨 STOP VEHICLE IMMEDIATELY! Seek professional service. Engine damage risk.'
    
    predicted_issue = detected_issues[0] if detected_issues else 'Normal Operation'
    
    return {
        'health_score': round(health_score, 1),
        'predicted_issue': predicted_issue,
        'recommendation': recommendation,
        'detected_issues': detected_issues
    }

# Send SMS Alert
def send_sms_alert(phone_number, message):
    if not twilio_enabled:
        print(f"📱 [SIMULATED] SMS to {phone_number}: {message[:100]}...")
        return True
    
    try:
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        sms = twilio_client.messages.create(
            body=message[:160],  # SMS length limit
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"✅ SMS sent to {phone_number}")
        return True
    except Exception as e:
        print(f"❌ SMS failed: {e}")
        return False

# Send Voice call Alert
def make_call_alert(phone_number, message):
    if not twilio_enabled:
        print(f"📞 [SIMULATED] Call to {phone_number}: {message}")
        return True
    
    try:
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        # Create TwiML for the call
        twiml = f'<Response><Say voice="alice">{message}</Say></Response>'
        
        call = twilio_client.calls.create(
            twiml=twiml,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"✅ Call initiated to {phone_number} (SID: {call.sid})")
        return True
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return False

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)
    return decorated

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    conn = get_db()
    status = 'connected' if conn else 'disconnected'
    if conn:
        conn.close()
    return jsonify({
        'status': 'healthy',
        'database': status,
        'twilio': 'enabled' if twilio_enabled else 'disabled',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/register', methods=['POST'])
def register():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (data['username'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'Username or email already exists'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, phone_number, password_hash, vehicle_model, vehicle_engine_cc) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['username'], 
            data['email'],
            data.get('phone_number', ''),
            password_hash.decode('utf-8'), 
            data.get('vehicle_model', ''),
            data.get('vehicle_engine_cc', 0)
        ))
        conn.commit()
        
        return jsonify({'message': 'User created successfully', 'user_id': cursor.lastrowid}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (data['username'],))
        user = cursor.fetchone()
        
        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user_id': user['id'],
            'username': user['username'],
            'vehicle_model': user['vehicle_model'],
            'email': user['email'],
            'phone_number': user.get('phone_number', '')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/engine-data', methods=['POST'])
@token_required
def submit_engine_data():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.json
        cursor = conn.cursor(dictionary=True)
        
        # Get user details
        cursor.execute("SELECT id, username, email, phone_number FROM users WHERE id = %s", (request.user_id,))
        user = cursor.fetchone()
        
        print(f"\n🔍 Analyzing engine data for user: {user['username']}")
        print(f"   Phone number in DB: {user.get('phone_number', 'NOT SET')}")
        
        # Get prediction
        prediction = predict_engine_health(data)
        print(f"   Health score: {prediction['health_score']}%")
        
        # Save reading
        cursor.execute("""
            INSERT INTO engine_readings 
            (user_id, engine_temp, rpm, speed, throttle_position, fuel_level,
             vibration, oxygen_sensor, knock_sensor, maf_sensor,
             predicted_health_score, predicted_issue, recommendation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.user_id,
            data.get('engine_temp'),
            data.get('rpm'),
            data.get('speed'),
            data.get('throttle_position'),
            data.get('fuel_level'),
            data.get('vibration'),
            data.get('oxygen_sensor'),
            data.get('knock_sensor'),
            data.get('maf_sensor'),
            prediction['health_score'],
            prediction['predicted_issue'],
            prediction['recommendation']
        ))
        
        reading_id = cursor.lastrowid
        conn.commit()
        
        # Send alerts
        alert_sent = False
        alert_methods = []
        
        if prediction['health_score'] < 60:
            if user.get('phone_number'):
                print(f"🚨 Health score {prediction['health_score']}% - Sending alerts to {user['phone_number']}")
                
                alert_msg = f"EngineEye Alert: Health {prediction['health_score']}%. {prediction['predicted_issue']}. {prediction['recommendation']}"
                
                # Send SMS
                if send_sms_alert(user['phone_number'], alert_msg):
                    alert_methods.append('sms')
                    alert_sent = True
                
                # Make call for critical alerts (health < 40)
                if prediction['health_score'] < 40:
                    call_msg = f"Critical engine alert. Health score {prediction['health_score']} percent. {prediction['predicted_issue']}. {prediction['recommendation']}"
                    if make_call_alert(user['phone_number'], call_msg):
                        alert_methods.append('call')
                
                # Save to database
                severity = 'critical' if prediction['health_score'] < 40 else 'high'
                cursor.execute("""
                    INSERT INTO alerts (user_id, reading_id, alert_type, severity, message)
                    VALUES (%s, %s, %s, %s, %s)
                """, (request.user_id, reading_id, prediction['predicted_issue'], severity, prediction['recommendation']))
                conn.commit()
            else:
                print("⚠️ No phone number - skipping alerts")
        else:
            print(f"✅ Health score {prediction['health_score']}% - No alert needed")
        
        return jsonify({
            'reading_id': reading_id,
            'prediction': prediction,
            'alert_sent': alert_sent,
            'alert_methods': alert_methods
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
@app.route('/api/engine-history', methods=['GET'])
@token_required
def get_engine_history():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        limit = request.args.get('limit', 50, type=int)
        
        cursor.execute("""
            SELECT id, timestamp, engine_temp, rpm, speed, predicted_health_score, predicted_issue, recommendation
            FROM engine_readings WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s
        """, (request.user_id, limit))
        
        readings = cursor.fetchall()
        for r in readings:
            r['timestamp'] = r['timestamp'].isoformat()
        
        return jsonify(readings)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts', methods=['GET'])
@token_required
def get_alerts():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        unresolved_only = request.args.get('unresolved', 'true').lower() == 'true'
        
        if unresolved_only:
            cursor.execute("""
                SELECT * FROM alerts WHERE user_id = %s AND is_resolved = FALSE ORDER BY created_at DESC
            """, (request.user_id,))
        else:
            cursor.execute("""
                SELECT * FROM alerts WHERE user_id = %s ORDER BY created_at DESC LIMIT 50
            """, (request.user_id,))
        
        alerts = cursor.fetchall()
        for a in alerts:
            a['created_at'] = a['created_at'].isoformat()
        
        return jsonify(alerts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['PUT'])
@token_required
def resolve_alert(alert_id):
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET is_resolved = TRUE WHERE id = %s AND user_id = %s", 
                      (alert_id, request.user_id))
        conn.commit()
        
        return jsonify({'message': 'Alert resolved successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/dashboard-stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Latest reading
        cursor.execute("""
            SELECT predicted_health_score, engine_temp, rpm 
            FROM engine_readings WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1
        """, (request.user_id,))
        latest = cursor.fetchone()
        
        # Unresolved alerts count
        cursor.execute("SELECT COUNT(*) as count FROM alerts WHERE user_id = %s AND is_resolved = FALSE", (request.user_id,))
        alert_count = cursor.fetchone()
        
        # Total readings
        cursor.execute("SELECT COUNT(*) as count FROM engine_readings WHERE user_id = %s", (request.user_id,))
        total_readings = cursor.fetchone()
        
        return jsonify({
            'latest_health': latest['predicted_health_score'] if latest else None,
            'latest_temp': latest['engine_temp'] if latest else None,
            'latest_rpm': latest['rpm'] if latest else None,
            'unresolved_alerts': alert_count['count'] if alert_count else 0,
            'total_readings': total_readings['count'] if total_readings else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("🔧 EngineEye Backend Server")
    print("=" * 50)
    print(f"Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"Twilio: {'Enabled' + ' - ' + TWILIO_PHONE_NUMBER if twilio_enabled else 'Disabled'}")
    print(f"Server: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000, host='0.0.0.0')