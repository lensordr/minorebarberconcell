import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import secrets
import requests
import json

load_dotenv()

def generate_cancel_token():
    return secrets.token_urlsafe(32)

def send_appointment_email(client_email, client_name, appointment_time, service_name, barber_name, cancel_token):
    try:
        cancel_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/cancel-appointment/{cancel_token}"
        
        body = f"""
Hello {client_name},

Your appointment has been confirmed at MINORE BARBER!

📅 APPOINTMENT DETAILS:
• Service: {service_name}
• Barber: {barber_name}
• Date & Time: {appointment_time.strftime('%A, %B %d, %Y at %I:%M %p')}

📍 LOCATION:
MINORE BARBER
Calle Mallorca 233

❌ NEED TO CANCEL?
Click here to cancel: {cancel_url}

📞 QUESTIONS?
Call us or reply to this email.

We look forward to seeing you!

Best regards,
MINORE BARBER Team
        """
        
        # Use SendGrid HTTP API instead of SMTP
        api_key = os.getenv('EMAIL_PASSWORD')  # SendGrid API key
        
        data = {
            "personalizations": [{
                "to": [{"email": client_email}],
                "subject": "MINORE BARBER - Appointment Confirmation"
            }],
            "from": {"email": os.getenv('EMAIL_FROM')},
            "content": [{"type": "text/plain", "value": body}]
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"Sending via SendGrid API to {client_email}")
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            data=json.dumps(data)
        )
        
        print(f"SendGrid API response: {response.status_code}")
        if response.status_code == 202:
            print("Email sent successfully via SendGrid API!")
            return True
        else:
            print(f"SendGrid API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Email error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def send_cancellation_email(client_email, client_name, appointment_time, service_name):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_FROM')
        msg['To'] = client_email
        msg['Subject'] = "MINORE BARBER - Appointment Cancelled"
        
        body = f"""
        Hello {client_name},

        Your appointment has been cancelled as requested.

        📅 CANCELLED APPOINTMENT:
        • Service: {service_name}
        • Date & Time: {appointment_time.strftime('%A, %B %d, %Y at %I:%M %p')}

        📝 WHAT'S NEXT?
        • Your time slot is now available for other customers
        • You can book a new appointment anytime at our website
        • No cancellation fees apply

        📞 QUESTIONS?
        Feel free to contact us if you need any assistance.

        We hope to see you again soon!
        
        Best regards,
        MINORE BARBER Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Cancellation email error: {e}")
        return False