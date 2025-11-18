#!/usr/bin/env python3
"""
Test Email Configuration for MINORE BARBER
This script tests if your email configuration is working correctly.
"""

from email_service import send_appointment_email, send_cancellation_email
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

def test_email_config():
    load_dotenv()
    
    print("=== MINORE BARBER - Email Configuration Test ===\n")
    
    # Check if email is configured
    if not all([os.getenv('EMAIL_HOST'), os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD')]):
        print("❌ Email not configured. Run 'python setup_email.py' first.")
        return
    
    test_email = input("Enter your email address to test: ").strip()
    if not test_email:
        print("❌ Email address required for testing.")
        return
    
    print(f"\n📧 Testing email configuration...")
    print(f"SMTP Host: {os.getenv('EMAIL_HOST')}")
    print(f"SMTP Port: {os.getenv('EMAIL_PORT')}")
    print(f"From Email: {os.getenv('EMAIL_FROM')}")
    
    # Test appointment confirmation email
    print(f"\n🔄 Sending test appointment confirmation email to {test_email}...")
    test_time = datetime.now() + timedelta(hours=2)
    
    success = send_appointment_email(
        client_email=test_email,
        client_name="Test Customer",
        appointment_time=test_time,
        service_name="Test Haircut",
        barber_name="Test Barber",
        cancel_token="test-token-123"
    )
    
    if success:
        print("✅ Appointment confirmation email sent successfully!")
    else:
        print("❌ Failed to send appointment confirmation email.")
        return
    
    # Test cancellation email
    print(f"\n🔄 Sending test cancellation email to {test_email}...")
    
    success = send_cancellation_email(
        client_email=test_email,
        client_name="Test Customer",
        appointment_time=test_time,
        service_name="Test Haircut"
    )
    
    if success:
        print("✅ Cancellation email sent successfully!")
        print(f"\n🎉 Email configuration is working correctly!")
        print(f"📬 Check your inbox at {test_email} for the test emails.")
    else:
        print("❌ Failed to send cancellation email.")

if __name__ == "__main__":
    test_email_config()