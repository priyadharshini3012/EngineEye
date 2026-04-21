# alert_service.py - SMS and Voice Call Alert System
import os
from twilio.rest import Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        # Get Twilio credentials from .env
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Check if Twilio is configured
        if self.account_sid and self.auth_token and self.twilio_phone:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                logger.info("✅ Twilio alert system initialized successfully")
                logger.info(f"   Phone number: {self.twilio_phone}")
            except Exception as e:
                self.enabled = False
                logger.error(f"❌ Twilio initialization failed: {e}")
        else:
            self.enabled = False
            logger.warning("⚠️ Twilio not configured. SMS/Calls will be simulated.")
    
    def send_sms(self, to_phone_number, message):
        """Send SMS alert using Twilio"""
        if not self.enabled:
            logger.info(f"📱 [SIMULATED] SMS to {to_phone_number}: {message[:100]}...")
            return True
        
        try:
            # Ensure phone number has +91 or country code
            if not to_phone_number.startswith('+'):
                to_phone_number = '+91' + to_phone_number  # Default India
            
            message = self.client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=to_phone_number
            )
            logger.info(f"✅ SMS sent to {to_phone_number}, SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"❌ SMS failed: {e}")
            return False
    
    def make_call(self, to_phone_number, message):
        """Make voice call alert using Twilio"""
        if not self.enabled:
            logger.info(f"📞 [SIMULATED] Call to {to_phone_number}: {message[:100]}...")
            return True
        
        try:
            # Ensure phone number has +91 or country code
            if not to_phone_number.startswith('+'):
                to_phone_number = '+91' + to_phone_number
            
            # Create TwiML for voice message
            twiml = f"""
            <Response>
                <Say voice="alice" language="en-IN">
                    {message}
                    Please check your EngineEye dashboard immediately.
                </Say>
            </Response>
            """
            
            call = self.client.calls.create(
                twiml=twiml,
                to=to_phone_number,
                from_=self.twilio_phone
            )
            logger.info(f"✅ Call initiated to {to_phone_number}, SID: {call.sid}")
            return True
        except Exception as e:
            logger.error(f"❌ Call failed: {e}")
            return False
    
    def send_engine_alert(self, user_phone, engine_data, prediction):
        """Send formatted engine alert based on health score"""
        health_score = prediction['health_score']
        
        # Format message based on severity
        if health_score < 40:
            severity = "CRITICAL"
            emoji = "🚨🚨🚨"
            sms_msg = f"{emoji} ENGINE EYE CRITICAL ALERT {emoji}\n\nHealth: {health_score}%\nIssue: {prediction['predicted_issue']}\n{prediction['recommendation']}\n\nSTOP VEHICLE IMMEDIATELY!"
            call_msg = f"Critical engine alert. Health score {health_score} percent. {prediction['predicted_issue']}. {prediction['recommendation']}. Please stop your vehicle immediately and check the EngineEye app."
            
            # Send both SMS and Call for critical alerts
            self.send_sms(user_phone, sms_msg)
            self.make_call(user_phone, call_msg)
            
        elif health_score < 60:
            severity = "HIGH"
            emoji = "⚠️⚠️"
            sms_msg = f"{emoji} ENGINE EYE HIGH ALERT {emoji}\n\nHealth: {health_score}%\nIssue: {prediction['predicted_issue']}\n{prediction['recommendation']}\n\nSchedule service immediately!"
            call_msg = f"High priority engine alert. Health score {health_score} percent. {prediction['predicted_issue']}. {prediction['recommendation']}. Please schedule immediate service."
            
            # Send SMS only for high alerts
            self.send_sms(user_phone, sms_msg)
            
        elif health_score < 75:
            severity = "MEDIUM"
            emoji = "⚠️"
            sms_msg = f"{emoji} ENGINE EYE ALERT {emoji}\n\nHealth: {health_score}%\nIssue: {prediction['predicted_issue']}\n{prediction['recommendation']}\n\nService recommended soon."
            
            # Send SMS for medium alerts
            self.send_sms(user_phone, sms_msg)
        
        else:
            severity = "GOOD"
            logger.info(f"✅ Engine health is good ({health_score}%). No alert needed.")
        
        return severity

# Test function
def test_alert_service():
    """Test the alert system with your phone number"""
    alert_service = AlertService()
    
    if alert_service.enabled:
        print("\n" + "="*50)
        print("Testing Alert Service")
        print("="*50)
        
        # Get your phone number
        phone = input("Enter your phone number with country code (e.g., +919876543210): ")
        
        print("\n1. Testing SMS...")
        alert_service.send_sms(phone, "EngineEye Test: Your alert system is working! 🔧")
        
        print("\n2. Testing Voice Call...")
        alert_service.make_call(phone, "This is a test call from EngineEye. Your alert system is working properly.")
        
        print("\n✅ Test complete! Check your phone.")
    else:
        print("\n❌ Twilio not configured. Please check your .env file.")
        print("Required variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")

if __name__ == "__main__":
    test_alert_service()