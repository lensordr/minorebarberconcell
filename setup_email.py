#!/usr/bin/env python3
"""
Email Configuration Setup for MINORE BARBER
This script helps you configure email settings for appointment notifications.
"""

import os
from dotenv import load_dotenv, set_key

def setup_email_config():
    print("=== MINORE BARBER - Email Configuration ===\n")
    
    # Load existing .env file
    load_dotenv()
    
    print("Configure your email settings for appointment notifications:")
    print("(Leave blank to keep current value)\n")
    
    # Get current values
    current_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    current_port = os.getenv('EMAIL_PORT', '587')
    current_user = os.getenv('EMAIL_USER', '')
    current_from = os.getenv('EMAIL_FROM', '')
    
    # Get new values
    email_host = input(f"SMTP Host [{current_host}]: ").strip() or current_host
    email_port = input(f"SMTP Port [{current_port}]: ").strip() or current_port
    email_user = input(f"Email Username [{current_user}]: ").strip() or current_user
    email_password = input("Email Password (App Password for Gmail): ").strip()
    email_from = input(f"From Email [{current_from or email_user}]: ").strip() or email_user
    
    # Base URL for cancellation links
    base_url = input("Base URL [http://localhost:8000]: ").strip() or "http://localhost:8000"
    
    # Update .env file
    env_file = '.env'
    set_key(env_file, 'EMAIL_HOST', email_host)
    set_key(env_file, 'EMAIL_PORT', email_port)
    set_key(env_file, 'EMAIL_USER', email_user)
    if email_password:
        set_key(env_file, 'EMAIL_PASSWORD', email_password)
    set_key(env_file, 'EMAIL_FROM', email_from)
    set_key(env_file, 'BASE_URL', base_url)
    
    print(f"\n✅ Email configuration saved to {env_file}")
    print("\n📧 Email Features Enabled:")
    print("• Appointment confirmation emails")
    print("• Cancellation confirmation emails")
    print("• Client-side appointment cancellation via email link")
    
    print("\n🔧 Gmail Setup Instructions:")
    print("1. Enable 2-Factor Authentication on your Gmail account")
    print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
    print("3. Use the App Password (not your regular password) in the configuration")
    
    print("\n🚀 Restart your application to apply the changes!")

if __name__ == "__main__":
    setup_email_config()