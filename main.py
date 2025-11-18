from fastapi import FastAPI, Request, Depends, HTTPException, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models, crud
from database import get_db
from email_service import send_appointment_email, generate_cancel_token, send_cancellation_email
import uvicorn
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import json
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager

def check_admin_auth(request: Request, admin_logged_in: str = Cookie(None)):
    if admin_logged_in != "true":
        return RedirectResponse(url="/admin/login", status_code=303)
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    print("Keep-alive active during business hours (10 AM - 8 PM)")
    print("MINORE BARBER - Ready for appointments!")
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="MINORE BARBER", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Simple refresh flag
last_booking_time = 0

# Auto-refresh disabled

# Create tables and ensure initial data
models.Base.metadata.create_all(bind=models.engine)

# Run database migration for email columns
try:
    import sqlite3
    conn = sqlite3.connect("barbershop.db")
    cursor = conn.cursor()
    
    # Check if email column exists
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'email' not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN email TEXT DEFAULT ''")
    
    if 'cancel_token' not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN cancel_token TEXT DEFAULT ''")
    
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Migration error: {e}")

# Ensure initial data exists only if database is empty
try:
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=models.engine)
    db = SessionLocal()
    
    # Only add default services if none exist
    if not crud.get_services(db):
        default_services = [
            ("Corte de pelo / Haircut", "Traditional scissor cut with styling", 30, 20.00),
            ("Arreglado Barba / Beard Trim", "Professional beard shaping and trimming", 30, 12.00),
            ("Corte + Barba Ritual / Haircut + Beard Ritual", "Complete grooming package", 60, 34.00),
            ("Corte Barba Express / Beard Trim Express", "Quick beard trim", 30, 25.00),
            ("Ritual Barba / Beard Ritual", "Full beard treatment", 30, 14.00)
        ]
        for service_name, description, duration, price in default_services:
            crud.create_service(db, service_name, duration, price, description)
    
    db.close()
except Exception as e:
    print(f"Initial data setup error: {e}")

# Keep-alive scheduler
scheduler = AsyncIOScheduler()

async def keep_alive():
    """Keep app alive during business hours (10 AM - 7 PM)"""
    import aiohttp
    import os
    
    current_hour = datetime.now().hour
    if 10 <= current_hour < 20:  # Only during business hours
        try:
            app_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:8000')
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{app_url}/") as response:
                    print(f"Keep-alive ping: {response.status} at {datetime.now().strftime('%H:%M')}")
        except Exception as e:
            print(f"Keep-alive error: {e}")

# Schedule keep-alive every 14 minutes
scheduler.add_job(
    keep_alive,
    'interval',
    minutes=14,
    id='keep_alive',
    replace_existing=True
)



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/test")
async def test_page():
    with open("test.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/test-dashboard")
async def test_dashboard():
    with open("test_dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/book", response_class=HTMLResponse)
async def book_appointment(request: Request, db: Session = Depends(get_db)):
    services = crud.get_services(db)
    barbers = crud.get_active_barbers(db)
    return templates.TemplateResponse("booking.html", {
        "request": request, 
        "services": services, 
        "barbers": barbers
    })

@app.post("/book")
async def create_appointment(
    request: Request,
    client_name: str = Form(...),
    client_email: str = Form(...),
    client_phone: str = Form(...),
    service_id: int = Form(...),
    barber_id: str = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Handle random barber selection
        if barber_id == "random":
            actual_barber_id = crud.get_barber_with_least_appointments(db, service_id, appointment_time)
            if not actual_barber_id:
                raise ValueError("No available barbers for this time slot")
        else:
            actual_barber_id = int(barber_id)
        
        appointment = crud.create_appointment(db, client_name, client_email, client_phone, service_id, actual_barber_id, appointment_time)
        # Mark as random appointment if it was randomly assigned
        if barber_id == "random":
            appointment.is_random = 1
            db.commit()
        # Get data before async thread
        service = crud.get_service_by_id(db, service_id)
        barber = crud.get_barber_by_id(db, actual_barber_id)
        
        # Test SendGrid email with async
        import threading
        import os
        def send_email_async():
            try:
                print(f"SendGrid: {os.getenv('EMAIL_HOST')}:{os.getenv('EMAIL_PORT')}")
                print(f"User: {os.getenv('EMAIL_USER')}")
                print(f"Sending to: {client_email}")
                success = send_appointment_email(client_email, client_name, appointment.appointment_time, service.name, barber.name, appointment.cancel_token)
                print(f"SendGrid result: {success}")
            except Exception as e:
                print(f"SendGrid error: {e}")
        
        threading.Thread(target=send_email_async, daemon=True).start()
        
        # Update refresh flag
        global last_booking_time
        import time
        last_booking_time = time.time()
        print(f"New booking created! Updated last_booking_time to {last_booking_time}")
        return RedirectResponse(url="/success", status_code=303)
    except ValueError:
        services = crud.get_services(db)
        barbers = crud.get_barbers(db)
        return templates.TemplateResponse("booking.html", {
            "request": request,
            "services": services,
            "barbers": barbers,
            "error": "Time slot already booked! Please select another time."
        })

@app.get("/success", response_class=HTMLResponse)
async def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login_post(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "minore123":
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie("admin_logged_in", "true")
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")



@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    print(f"Dashboard accessed at {datetime.now()}")
    appointments = crud.get_today_appointments_ordered(db)
    barbers = crud.get_barbers_with_revenue(db)
    services = crud.get_services(db)
    schedule = crud.get_schedule(db)
    counts = crud.get_today_appointment_counts(db)
    
    # Create grid data with appointment spans
    from grid_helper import create_appointment_grid
    grid_data = create_appointment_grid(db, appointments, schedule)
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "appointments": appointments,
        "barbers": crud.get_active_barbers(db),
        "all_barbers": barbers,
        "services": services,
        "schedule": schedule,
        "counts": counts,
        "grid_data": grid_data,
        "now": datetime.now()
    })

@app.get("/admin/staff", response_class=HTMLResponse)
async def staff_management(request: Request, db: Session = Depends(get_db)):
    barbers = crud.get_barbers(db)
    services = crud.get_services(db)
    schedule = crud.get_schedule(db)
    return templates.TemplateResponse("staff_management.html", {
        "request": request,
        "barbers": barbers,
        "services": services,
        "schedule": schedule
    })

@app.post("/admin/add-barber")
async def add_barber(name: str = Form(...), db: Session = Depends(get_db), auth: bool = Depends(check_admin_auth)):
    crud.create_barber(db, name)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/delete-barber/{barber_id}")
async def delete_barber(barber_id: int, db: Session = Depends(get_db), auth: bool = Depends(check_admin_auth)):
    crud.delete_barber(db, barber_id)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/toggle-barber/{barber_id}")
async def toggle_barber(barber_id: int, db: Session = Depends(get_db)):
    crud.toggle_barber_status(db, barber_id)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/add-service")
async def add_service(
    name: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db),
    auth: bool = Depends(check_admin_auth)
):
    crud.create_service(db, name, duration, price, description)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/edit-service/{service_id}")
async def edit_service(
    service_id: int,
    name: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db),
    auth: bool = Depends(check_admin_auth)
):
    crud.update_service(db, service_id, name, duration, price, description)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/delete-service/{service_id}")
async def delete_service(service_id: int, db: Session = Depends(get_db), auth: bool = Depends(check_admin_auth)):
    crud.delete_service(db, service_id)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/checkout/{appointment_id}")
async def checkout_appointment(appointment_id: int, db: Session = Depends(get_db)):
    crud.checkout_appointment(db, appointment_id)
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.post("/admin/cancel/{appointment_id}")
async def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    crud.cancel_appointment(db, appointment_id)
    return RedirectResponse(url="/admin/dashboard", status_code=303)



@app.post("/admin/edit-appointment")
async def edit_appointment(
    appointment_id: int = Form(...),
    time: str = Form(...),
    price: float = Form(...),
    duration: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        crud.update_appointment_details(db, appointment_id, time, price, duration)
        return {"success": True, "message": "Appointment updated successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}

@app.post("/admin/add-appointment")
async def add_manual_appointment(
    client_name: str = Form(...),
    service_id: int = Form(...),
    barber_id: int = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Admin can create appointments at any time - bypass time validation
        crud.create_appointment_admin(db, client_name, "", service_id, barber_id, appointment_time)
        # Trigger dashboard refresh
        from refresh_trigger import trigger_dashboard_refresh
        trigger_dashboard_refresh()
        return {"success": True, "message": f"Appointment added for {client_name}"}
    except ValueError:
        return {"success": False, "message": "Time slot already taken"}

@app.post("/admin/update-schedule")
async def update_schedule(
    start_hour: int = Form(...),
    end_hour: int = Form(...),
    db: Session = Depends(get_db),
    auth: bool = Depends(check_admin_auth)
):
    crud.update_schedule(db, start_hour, end_hour)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/cleanup")
async def cleanup_daily(db: Session = Depends(get_db)):
    cleaned = crud.cleanup_daily_and_save_revenue(db)
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.get("/admin/revenue", response_class=HTMLResponse)
async def revenue_reports(request: Request, view: str = "monthly", date: str = None, revenue_logged_in: str = Cookie(None), db: Session = Depends(get_db)):
    # Only ask for password if not logged in AND it's the main revenue access (no view parameter from URL)
    if revenue_logged_in != "true" and not request.url.query:
        return templates.TemplateResponse("revenue_login.html", {"request": request})
    
    if view == "daily":
        revenue_data = crud.get_daily_revenue(db, date)
        template = "daily_revenue.html"
    elif view == "weekly":
        revenue_data = crud.get_weekly_revenue(db, date)
        template = "weekly_revenue.html"
    else:
        revenue_data = crud.get_monthly_revenue(db)
        template = "monthly_revenue.html"
    
    return templates.TemplateResponse(template, {
        "request": request,
        "revenue_data": revenue_data,
        "current_view": view,
        "selected_date": date or datetime.now().strftime('%Y-%m-%d')
    })

@app.post("/admin/revenue-login")
async def revenue_login_post(request: Request, password: str = Form(...), db: Session = Depends(get_db)):
    if password == "minorebarber2025":
        response = RedirectResponse(url="/admin/revenue", status_code=303)
        response.set_cookie("revenue_logged_in", "true")  # Session-based
        return response
    else:
        return templates.TemplateResponse("revenue_login.html", {
            "request": request,
            "error": "Invalid password"
        })

@app.get("/admin/revenue-logout")
async def revenue_logout():
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.delete_cookie("revenue_logged_in")
    return response

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_logged_in")
    return response

@app.get("/api/available-times/{barber_id}/{service_id}")
async def get_available_times(barber_id: int, service_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import JSONResponse
    times = crud.get_available_times_for_service(db, barber_id, service_id)
    return JSONResponse(
        content=times,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/cancel-appointment/{cancel_token}")
async def cancel_appointment_by_token(request: Request, cancel_token: str, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(
        models.Appointment.cancel_token == cancel_token,
        models.Appointment.status == "scheduled"
    ).first()
    
    return templates.TemplateResponse("cancel_appointment.html", {
        "request": request,
        "appointment": appointment,
        "cancel_token": cancel_token
    })

@app.post("/cancel-appointment/{cancel_token}/confirm")
async def confirm_cancel_appointment(request: Request, cancel_token: str, db: Session = Depends(get_db)):
    appointment = db.query(models.Appointment).filter(
        models.Appointment.cancel_token == cancel_token,
        models.Appointment.status == "scheduled"
    ).first()
    
    if appointment:
        appointment.status = "cancelled"
        db.commit()
        
        # Send cancellation confirmation email
        send_cancellation_email(appointment.email, appointment.client_name, appointment.appointment_time, appointment.service.name)
        
        return templates.TemplateResponse("cancel_success.html", {"request": request})
    else:
        return templates.TemplateResponse("cancel_appointment.html", {
            "request": request,
            "appointment": None,
            "cancel_token": cancel_token
        })

@app.get("/api/check-refresh")
async def check_refresh(last_check: float = 0):
    global last_booking_time
    refresh_needed = last_booking_time > last_check
    print(f"Refresh check: last_booking={last_booking_time}, last_check={last_check}, refresh_needed={refresh_needed}")
    return {"refresh_needed": refresh_needed, "timestamp": last_booking_time}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)