import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import models, crud
import os
from database_postgres import SessionLocal

async def send_daily_revenue_email():
    """Send daily revenue report via email"""
    try:
        # Email configuration (using existing SendGrid setup)
        smtp_server = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
        smtp_port = int(os.environ.get('EMAIL_PORT', '587'))
        smtp_username = os.environ.get('EMAIL_USER', 'apikey')
        smtp_password = os.environ.get('EMAIL_PASSWORD', '')
        from_email = os.environ.get('EMAIL_FROM', 'minorebarbereixample@gmail.com')
        to_email = "minorebarbereixample@gmail.com"
        
        if not smtp_username or not smtp_password:
            print("Email not configured - skipping daily revenue email")
            return
    except Exception as e:
        print(f"Email configuration error: {e}")
        return
    
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get revenue data
    db = SessionLocal()
    
    try:
        # Get daily revenue for yesterday
        daily_revenue = db.query(models.DailyRevenue).filter(
            models.DailyRevenue.date == yesterday
        ).all()
        
        # Get barber names
        barbers = {b.id: b.name for b in db.query(models.Barber).all()}
        
        # Create email content
        subject = f"Daily Revenue Report - {yesterday}"
        
        html_content = f"""
        <html>
        <body>
            <h2>MINORE BARBER - Daily Revenue Report</h2>
            <h3>Date: {yesterday}</h3>
            
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px;">Barber</th>
                    <th style="padding: 10px;">Revenue (€)</th>
                    <th style="padding: 10px;">Appointments</th>
                </tr>
        """
        
        total_revenue = 0
        total_appointments = 0
        
        for revenue in daily_revenue:
            barber_name = barbers.get(revenue.barber_id, "Unknown")
            html_content += f"""
                <tr>
                    <td style="padding: 10px;">{barber_name}</td>
                    <td style="padding: 10px;">€{revenue.revenue:.2f}</td>
                    <td style="padding: 10px;">{revenue.appointments_count}</td>
                </tr>
            """
            total_revenue += revenue.revenue
            total_appointments += revenue.appointments_count
        
        html_content += f"""
                <tr style="background-color: #f2f2f2; font-weight: bold;">
                    <td style="padding: 10px;">TOTAL</td>
                    <td style="padding: 10px;">€{total_revenue:.2f}</td>
                    <td style="padding: 10px;">{total_appointments}</td>
                </tr>
            </table>
            
            <p><small>Generated automatically by MINORE BARBER system</small></p>
        </body>
        </html>
        """
        
        # Send email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"Daily revenue email sent successfully for {yesterday}")
        
    except Exception as e:
        print(f"Error sending daily revenue email: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    send_daily_revenue_email()