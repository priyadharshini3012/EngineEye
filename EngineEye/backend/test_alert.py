# test_alert.py - Test your Twilio integration
from alert_service import AlertService, test_alert_service

if __name__ == "__main__":
    print("="*50)
    print("EngineEye - Twilio Alert Test")
    print("="*50)
    
    # Initialize service
    alert_service = AlertService()
    
    if alert_service.enabled:
        print("\n✅ Twilio is configured!")
        print(f"   Account SID: {alert_service.account_sid[:10]}...")
        print(f"   Phone Number: {alert_service.twilio_phone}")
        
        # Run interactive test
        test_alert_service()
    else:
        print("\n❌ Twilio configuration missing!")
        print("\nPlease create .env file with:")
        print("TWILIO_ACCOUNT_SID=your_sid_here")
print("TWILIO_AUTH_TOKEN=your_token_here")
print("TWILIO_PHONE_NUMBER=your_number_here")