import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import secrets

load_dotenv()

def generate_cancel_token():
    return secrets.token_urlsafe(32)

def send_appointment_email(client_email, client_name, appointment_time, service_name, barber_name, cancel_token):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_FROM')
        msg['To'] = client_email
        msg['Subject'] = "MINORE BARBER - Appointment Confirmation"
        
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
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
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