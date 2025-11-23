# MINORE BARBERSHOP - Appointment System

A modern, minimalist web-based appointment system for barbershops.

## Features

### Customer Features
- 📱 QR code access for easy booking
- ⏰ Same-day appointment scheduling
- 💇 Service selection with pricing
- 👨‍💼 Barber selection
- 📞 Contact information collection (email + phone)
- 📧 Email confirmation with appointment details
- ❌ Client-side appointment cancellation via email link

### Admin Features
- 📊 Real-time appointment dashboard (ordered by time)
- 💳 One-click checkout system
- ❌ Appointment cancellation
- 👥 Staff management
- 💰 Live revenue tracking per barber
- 📋 Today's schedule overview
- 📱 QR code generation for easy access

## Quick Start

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup database**
```bash
python setup.py
```

3. **Configure email (optional)**
```bash
python setup_email.py
```

4. **Test email configuration (optional)**
```bash
python test_email.py
```

5. **Run the application**
```bash
python main.py
```

4. **Access the system**
- Customer booking: http://localhost:8000/book
- Admin dashboard: http://localhost:8000/admin/login
- Default login: admin / minore123

## Project Structure
```
MinoreBarbershop/
├── main.py              # FastAPI application
├── models.py            # Database models
├── crud.py              # Database operations
├── database.py          # Database session
├── setup.py             # Initial setup
├── static/
│   ├── css/style.css    # Modern styling
│   └── js/app.js        # JavaScript
├── templates/           # HTML templates
└── requirements.txt     # Dependencies
```

## Usage

### For Customers
1. Scan QR code or visit booking URL
2. Enter name, email, and phone number
3. Select desired service
4. Choose preferred barber
5. Pick available time slot
6. Confirm appointment
7. Receive email confirmation with cancellation link
8. Cancel via email link if needed

### For Admin
1. Login to admin dashboard
2. View today's appointments (ordered by time)
3. Complete appointments with one-click checkout
4. Cancel appointments if needed
5. Track live revenue by barber
6. Manage staff members
7. Monitor real-time bookings

## Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Modern minimalist design

## Key Features Added

### ✅ Checkout System
- Complete appointments with "Complete & Checkout" button
- Automatic revenue calculation
- Real-time revenue tracking per barber

### 📅 Appointment Management
- Appointments ordered by time (earliest first)
- Cancel appointments with confirmation
- Status tracking (scheduled/completed/cancelled)

### 📱 QR Code Access
- Auto-generated QR code for easy customer access
- Points directly to booking page

### 📧 Email Notifications
- Automatic appointment confirmation emails
- Professional email templates with appointment details
- Client-side cancellation via secure email links
- Cancellation confirmation emails
- Easy email configuration setup

## Default Data
- **Barbers**: Marco Silva, Antonio Rodriguez, Carlos Mendez
- **Services**: Classic Haircut ($25), Beard Trim ($15), Hair + Beard ($35), etc.
- **Hours**: 9:00 AM - 6:00 PM (30-minute slots)
- **Admin Login**: admin / minore123

---
Built for MINORE BARBERSHOP# Force redeploy
