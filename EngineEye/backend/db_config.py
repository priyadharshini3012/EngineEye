# db_config.py
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'engineeye')
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("✅ Connected to MySQL database")
                return True
        except Error as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
    
    # User Management
    def create_user(self, username, email, password, vehicle_model='', vehicle_engine_cc=0):
        """Register new user"""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            query = """INSERT INTO users (username, email, password_hash, vehicle_model, vehicle_engine_cc) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (username, email, password_hash.decode('utf-8'), vehicle_model, vehicle_engine_cc)
            
            self.cursor.execute(query, values)
            self.connection.commit()
            
            return {'success': True, 'user_id': self.cursor.lastrowid}
        except Error as e:
            return {'success': False, 'message': str(e)}
    
    def authenticate_user(self, username, password):
        """Login user"""
        try:
            query = "SELECT * FROM users WHERE username = %s"
            self.cursor.execute(query, (username,))
            user = self.cursor.fetchone()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return {'success': True, 'user': user}
            return {'success': False, 'message': 'Invalid credentials'}
        except Error as e:
            return {'success': False, 'message': str(e)}
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            query = "SELECT id, username, email, vehicle_model, vehicle_engine_cc FROM users WHERE id = %s"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
            return None
    
    # Engine Readings
    def save_engine_reading(self, user_id, sensor_data, prediction):
        """Save engine reading with AI prediction"""
        try:
            query = """INSERT INTO engine_readings 
                       (user_id, engine_temp, rpm, speed, throttle_position, fuel_level,
                        vibration, oxygen_sensor, knock_sensor, maf_sensor,
                        predicted_health_score, predicted_issue, recommendation)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            values = (user_id,
                     sensor_data.get('engine_temp'),
                     sensor_data.get('rpm'),
                     sensor_data.get('speed'),
                     sensor_data.get('throttle_position'),
                     sensor_data.get('fuel_level'),
                     sensor_data.get('vibration'),
                     sensor_data.get('oxygen_sensor'),
                     sensor_data.get('knock_sensor'),
                     sensor_data.get('maf_sensor'),
                     prediction['health_score'],
                     prediction['predicted_issue'],
                     prediction['recommendation'])
            
            self.cursor.execute(query, values)
            self.connection.commit()
            reading_id = self.cursor.lastrowid
            
            # Create alert if health score is low
            if prediction['health_score'] < 60:
                severity = 'critical' if prediction['health_score'] < 40 else 'high'
                self.create_alert(user_id, reading_id, prediction['predicted_issue'], 
                                 severity, prediction['recommendation'])
            
            return {'success': True, 'reading_id': reading_id}
        except Error as e:
            return {'success': False, 'message': str(e)}
    
    def get_engine_history(self, user_id, limit=50):
        """Get user's engine history"""
        try:
            query = """SELECT id, timestamp, engine_temp, rpm, speed, 
                              predicted_health_score, predicted_issue, recommendation
                       FROM engine_readings WHERE user_id = %s 
                       ORDER BY timestamp DESC LIMIT %s"""
            self.cursor.execute(query, (user_id, limit))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
            return []
    
    def get_latest_reading(self, user_id):
        """Get latest engine reading"""
        try:
            query = "SELECT * FROM engine_readings WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error: {e}")
            return None
    
    def get_dashboard_stats(self, user_id):
        """Get dashboard statistics"""
        try:
            stats = {}
            
            # Latest reading
            latest = self.get_latest_reading(user_id)
            stats['latest_health'] = latest['predicted_health_score'] if latest else None
            stats['latest_temp'] = latest['engine_temp'] if latest else None
            stats['latest_rpm'] = latest['rpm'] if latest else None
            
            # Average health of last 10 readings
            query = """SELECT AVG(predicted_health_score) as avg_health 
                       FROM (SELECT predicted_health_score FROM engine_readings 
                             WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10) as recent"""
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            stats['avg_health_score'] = float(result['avg_health']) if result['avg_health'] else 0
            
            # Unresolved alerts count
            query = "SELECT COUNT(*) as count FROM alerts WHERE user_id = %s AND is_resolved = FALSE"
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            stats['unresolved_alerts'] = result['count'] if result else 0
            
            # Total readings
            query = "SELECT COUNT(*) as count FROM engine_readings WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            stats['total_readings'] = result['count'] if result else 0
            
            # Health trend (last 7 readings)
            query = """SELECT predicted_health_score FROM engine_readings 
                       WHERE user_id = %s ORDER BY timestamp DESC LIMIT 7"""
            self.cursor.execute(query, (user_id,))
            readings = self.cursor.fetchall()
            stats['health_trend'] = [r['predicted_health_score'] for r in reversed(readings)]
            
            return stats
        except Error as e:
            print(f"Error: {e}")
            return {}
    
    # Alerts Management
    def create_alert(self, user_id, reading_id, alert_type, severity, message):
        """Create new alert"""
        try:
            query = """INSERT INTO alerts (user_id, reading_id, alert_type, severity, message) 
                       VALUES (%s, %s, %s, %s, %s)"""
            self.cursor.execute(query, (user_id, reading_id, alert_type, severity, message))
            self.connection.commit()
            return {'success': True}
        except Error as e:
            print(f"Error: {e}")
            return {'success': False}
    
    def get_alerts(self, user_id, unresolved_only=True):
        """Get user alerts"""
        try:
            if unresolved_only:
                query = "SELECT * FROM alerts WHERE user_id = %s AND is_resolved = FALSE ORDER BY created_at DESC"
            else:
                query = "SELECT * FROM alerts WHERE user_id = %s ORDER BY created_at DESC LIMIT 50"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
            return []
    
    def resolve_alert(self, alert_id, user_id):
        """Mark alert as resolved"""
        try:
            query = "UPDATE alerts SET is_resolved = TRUE WHERE id = %s AND user_id = %s"
            self.cursor.execute(query, (alert_id, user_id))
            self.connection.commit()
            return {'success': True}
        except Error as e:
            return {'success': False, 'message': str(e)}

# Global instance
db = None

def get_db():
    global db
    if db is None:
        db = DatabaseManager()
        db.connect()
    return db