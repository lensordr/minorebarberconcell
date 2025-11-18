#!/usr/bin/env python3
"""
Quick email test - sends test emails immediately
"""

from email_service import send_appointment_email, send_cancellation_email
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Test email
test_email = input("Enter your email to test: ").strip()
if not test_email:
    print("Email required")
    exit()

print("🔄 Sending test appointment confirmation...")
success = send_appointment_email(
    client_email=test_email,
    client_name="Test Customer",
    appointment_time=datetime.now() + timedelta(hours=2),
    service_name="Test Haircut",
    barber_name="Test Barber",
    cancel_token="test-cancel-123"
)

if success:
    print("✅ Confirmation email sent!")
else:
    print("❌ Email failed - check your .env configuration")

print("🔄 Sending test cancellation email...")
success = send_cancellation_email(
    client_email=test_email,
    client_name="Test Customer", 
    appointment_time=datetime.now() + timedelta(hours=2),
    service_name="Test Haircut"
)

if success:
    print("✅ Cancellation email sent!")
    print(f"📬 Check your inbox at {test_email}")
else:
    print("❌ Cancellation email failed")