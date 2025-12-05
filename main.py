from fastapi import FastAPI, Request, Depends, HTTPException, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models, crud, os
from database_postgres import get_db
from email_service import send_appointment_email, generate_cancel_token, send_cancellation_email
import uvicorn
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import json
from sse_starlette.sse import EventSourceResponse
from contextlib import asynccontextmanager
import io

def check_admin_auth(request: Request, admin_logged_in: str = Cookie(None)):
    if admin_logged_in != "true":
        return RedirectResponse(url="/admin/login", status_code=303)
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    print("Keep-alive active during business hours (10 AM - 10 PM)")
    print("MINORE BARBER - Ready for appointments!")
    yield
    # Shutdown
    try:
        scheduler.shutdown(wait=False)
    except Exception as e:
        print(f"Scheduler shutdown error (ignored): {e}")

app = FastAPI(title="MINORE BARBER", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Simple refresh flag
last_booking_time = 0

# Auto-refresh disabled

# Tables created manually - no auto-creation to preserve data

# Keep-alive scheduler
scheduler = AsyncIOScheduler()

async def keep_alive():
    """Keep app alive during business hours (10 AM - 8 PM CET)"""
    import aiohttp
    import os
    from datetime import timezone, timedelta
    
    # Use CET timezone (UTC+1, UTC+2 in summer)
    cet = timezone(timedelta(hours=1))
    current_time = datetime.now(cet)
    current_hour = current_time.hour
    
    print(f"Keep-alive check: CET time {current_time.strftime('%H:%M')}, hour={current_hour}")
    
    if 10 <= current_hour < 22:  # Only during business hours CET
        try:
            app_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:8000')
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{app_url}/") as response:
                    print(f"Keep-alive ping: {response.status} at {current_time.strftime('%H:%M')} CET")
        except Exception as e:
            print(f"Keep-alive error: {e}")
    else:
        print(f"Outside business hours ({current_hour}:00 CET) - skipping keep-alive")

# Schedule keep-alive every 14 minutes
scheduler.add_job(
    keep_alive,
    'interval',
    minutes=14,
    id='keep_alive',
    replace_existing=True
)

# Schedule daily revenue email at 9 AM
from daily_revenue_email import send_daily_revenue_email
scheduler.add_job(
    send_daily_revenue_email,
    'cron',
    hour=9,
    minute=0,
    id='daily_revenue_email',
    replace_existing=True
)



def check_business_hours():
    from datetime import timezone, timedelta
    cet = timezone(timedelta(hours=1))
    current_time = datetime.now(cet)
    return 10 <= current_time.hour < 22

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not check_business_hours():
        return HTMLResponse("<h1>MINORE BARBERSHOP</h1><p>We are closed. Open 11:00 - 20:00</p><style>body{font-family:Arial;text-align:center;padding:50px;background:#1d1a1c;color:#fbcc93;}</style>")
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/locations", response_class=HTMLResponse)
async def location_selector(request: Request):
    return templates.TemplateResponse("location_selector.html", {"request": request})

@app.get("/test")
async def test_page():
    with open("test.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/test-dashboard")
async def test_dashboard():
    with open("test_dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/mallorca/book", response_class=HTMLResponse)
async def book_appointment_mallorca(request: Request, db: Session = Depends(get_db)):
    if not check_business_hours():
        return HTMLResponse("<h1>MINORE BARBERSHOP - MALLORCA</h1><p>We are closed. Open 11:00 - 20:00</p><style>body{font-family:Arial;text-align:center;padding:50px;background:#1d1a1c;color:#fbcc93;}</style>")
    
    schedule = crud.get_schedule(db)
    if not schedule.is_open:
        return HTMLResponse("<h1>MINORE BARBERSHOP - MALLORCA</h1><p>We are temporarily closed. Please check back later.</p><style>body{font-family:Arial;text-align:center;padding:50px;background:#1d1a1c;color:#fbcc93;}</style>")
    
    services = crud.get_services_by_location(db, 1)
    barbers = crud.get_active_barbers_by_location(db, 1)
    return templates.TemplateResponse("booking.html", {
        "request": request, 
        "services": services, 
        "barbers": barbers,
        "location": "Mallorca",
        "location_id": 1
    })

@app.get("/concell/book", response_class=HTMLResponse)
async def book_appointment_concell(request: Request, db: Session = Depends(get_db)):
    if not check_business_hours():
        return HTMLResponse("<h1>MINORE BARBERSHOP - CONCELL</h1><p>We are closed. Open 11:00 - 20:00</p><style>body{font-family:Arial;text-align:center;padding:50px;background:#1d1a1c;color:#fbcc93;}</style>")
    
    schedule = crud.get_schedule(db)
    if not schedule.is_open:
        return HTMLResponse("<h1>MINORE BARBERSHOP - CONCELL</h1><p>We are temporarily closed. Please check back later.</p><style>body{font-family:Arial;text-align:center;padding:50px;background:#1d1a1c;color:#fbcc93;}</style>")
    
    services = crud.get_services_by_location(db, 2)
    barbers = crud.get_active_barbers_by_location(db, 2)
    return templates.TemplateResponse("booking.html", {
        "request": request, 
        "services": services, 
        "barbers": barbers,
        "location": "Concell",
        "location_id": 2
    })

@app.get("/book", response_class=HTMLResponse)
async def book_appointment_redirect(request: Request, db: Session = Depends(get_db)):
    default_location = int(os.environ.get('DEFAULT_LOCATION', 1))
    if default_location == 1:
        return RedirectResponse(url="/mallorca/book", status_code=303)
    else:
        return RedirectResponse(url="/concell/book", status_code=303)

@app.post("/mallorca/book")
async def create_appointment_mallorca(
    request: Request,
    client_name: str = Form(...),
    client_email: str = Form(""),
    client_phone: str = Form(...),
    service_id: int = Form(...),
    barber_id: str = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
):
    return await create_appointment_helper(request, client_name, client_email, client_phone, service_id, barber_id, appointment_time, 1, db)

@app.post("/concell/book")
async def create_appointment_concell(
    request: Request,
    client_name: str = Form(...),
    client_email: str = Form(""),
    client_phone: str = Form(...),
    service_id: int = Form(...),
    barber_id: str = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
):
    return await create_appointment_helper(request, client_name, client_email, client_phone, service_id, barber_id, appointment_time, 2, db)

async def create_appointment_helper(
    request: Request,
    client_name: str,
    client_email: str,
    client_phone: str,
    service_id: int,
    barber_id: str,
    appointment_time: str,
    location_id: int,
    db: Session
):
    try:
        # Handle random barber selection
        if barber_id == "random":
            actual_barber_id = crud.get_barber_with_least_appointments(db, service_id, appointment_time, location_id)
            if not actual_barber_id:
                raise ValueError("No available barbers for this time slot")
        else:
            actual_barber_id = int(barber_id)
        
        appointment = crud.create_appointment(db, client_name, client_email, client_phone, service_id, actual_barber_id, appointment_time)
        # Mark as random appointment if it was randomly assigned
        if barber_id == "random":
            appointment.is_random = 1
            db.commit()
        # Send email only if provided
        if client_email and client_email.strip():
            service = crud.get_service_by_id(db, service_id)
            barber = crud.get_barber_by_id(db, actual_barber_id)
            
            import threading
            def send_email_async():
                try:
                    print(f"Sending confirmation email to: {client_email}")
                    location_name = "Mallorca" if location_id == 1 else "Concell"
                    success = send_appointment_email(client_email, client_name, appointment.appointment_time, service.name, barber.name, appointment.cancel_token, location_name)
                    print(f"Email result: {success}")
                except Exception as e:
                    print(f"Email error: {e}")
            
            threading.Thread(target=send_email_async, daemon=True).start()
        else:
            print(f"No email provided - appointment created without email notification")
        
        # Update refresh flag
        global last_booking_time
        import time
        last_booking_time = time.time()
        print(f"New booking created! Updated last_booking_time to {last_booking_time}")
        # Redirect with email parameter
        email_param = "true" if client_email and client_email.strip() else "false"
        location_path = "mallorca" if location_id == 1 else "concell"
        return RedirectResponse(url=f"/{location_path}/success?email={email_param}", status_code=303)
    except ValueError:
        services = crud.get_services_by_location(db, location_id)
        barbers = crud.get_active_barbers_by_location(db, location_id)
        location_name = "Mallorca" if location_id == 1 else "Concell"
        return templates.TemplateResponse("booking.html", {
            "request": request,
            "services": services,
            "barbers": barbers,
            "location": location_name,
            "location_id": location_id,
            "error": "Time slot already booked! Please select another time."
        })

@app.get("/mallorca/success", response_class=HTMLResponse)
async def success_mallorca(request: Request):
    return templates.TemplateResponse("success.html", {"request": request, "location": "Mallorca"})

@app.get("/concell/success", response_class=HTMLResponse)
async def success_concell(request: Request):
    return templates.TemplateResponse("success.html", {"request": request, "location": "Concell"})

@app.get("/success", response_class=HTMLResponse)
async def success_redirect(request: Request):
    return RedirectResponse(url="/locations", status_code=303)

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
async def admin_dashboard(request: Request, location: int = None, db: Session = Depends(get_db)):
    if location is None:
        location = int(os.environ.get('DEFAULT_LOCATION', 1))
    print(f"Dashboard accessed at {datetime.now()} for location {location}")
    appointments = crud.get_today_appointments_ordered_by_location(db, location)
    barbers = crud.get_barbers_with_revenue_by_location(db, location)
    services = crud.get_services_by_location(db, location)
    schedule = crud.get_schedule(db)
    counts = crud.get_today_appointment_counts_by_location(db, location)
    
    # Create grid data with appointment spans
    from grid_helper import create_appointment_grid
    grid_data = create_appointment_grid(db, appointments, schedule, location)
    
    location_name = "Mallorca" if location == 1 else "Concell"
    
    active_barbers = crud.get_active_barbers_by_location(db, location)
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "appointments": appointments,
        "barbers": active_barbers,
        "all_barbers": barbers,
        "services": services,
        "schedule": schedule,
        "counts": counts,
        "grid_data": grid_data,
        "now": datetime.now(),
        "location": location_name,
        "location_id": location
    })

@app.get("/admin/staff", response_class=HTMLResponse)
async def staff_management(request: Request, location: int = None, db: Session = Depends(get_db)):
    if location is None:
        location = int(os.environ.get('DEFAULT_LOCATION', 1))
    
    barbers = crud.get_barbers_with_revenue_by_location(db, location)
    services = crud.get_services_by_location(db, location)
    schedule = crud.get_schedule(db)
    location_name = "Mallorca" if location == 1 else "Concell"
    
    return templates.TemplateResponse("staff_management.html", {
        "request": request,
        "barbers": barbers,
        "services": services,
        "schedule": schedule,
        "location": location_name,
        "location_id": location
    })

@app.post("/admin/add-barber")
async def add_barber(name: str = Form(...), db: Session = Depends(get_db), auth: bool = Depends(check_admin_auth)):
    location_id = int(os.environ.get('DEFAULT_LOCATION', 1))
    crud.create_barber(db, name, location_id)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/delete-barber/{barber_id}")
async def delete_barber(barber_id: int, db: Session = Depends(get_db), auth: bool = Depends(check_admin_auth)):
    crud.delete_barber(db, barber_id)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/toggle-barber/{barber_id}")
async def toggle_barber(barber_id: int, db: Session = Depends(get_db)):
    crud.toggle_barber_status(db, barber_id)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/edit-barber/{barber_id}")
async def edit_barber(barber_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    crud.update_barber_name(db, barber_id, name)
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
    location_id = int(os.environ.get('DEFAULT_LOCATION', 1))
    crud.create_service(db, name, duration, price, description, location_id)
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

@app.post("/admin/reopen/{appointment_id}")
async def reopen_appointment(appointment_id: int, db: Session = Depends(get_db)):
    crud.reopen_appointment(db, appointment_id)
    return RedirectResponse(url="/admin/dashboard", status_code=303)



@app.post("/admin/edit-appointment")
async def edit_appointment(
    appointment_id: int = Form(...),
    client_name: str = Form(...),
    barber_id: int = Form(...),
    time: str = Form(...),
    price: float = Form(...),
    duration: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        crud.update_appointment_details(db, appointment_id, client_name, barber_id, time, price, duration)
        return {"success": True, "message": "Appointment updated successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}

@app.post("/admin/add-appointment")
async def add_manual_appointment(
    client_name: str = Form(...),
    service_id: int = Form(...),
    barber_id: int = Form(...),
    appointment_time: str = Form(...),
    duration: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Admin can create appointments at any time - bypass time validation
        appointment = crud.create_appointment_admin(db, client_name, "", service_id, barber_id, appointment_time)
        
        # Set custom duration and price
        appointment.custom_duration = duration
        appointment.custom_price = price
        db.commit()
        
        # Trigger dashboard refresh
        global last_booking_time
        import time
        last_booking_time = time.time()
        print(f"Admin appointment created! Updated last_booking_time to {last_booking_time}")
        
        return {"success": True, "message": f"Appointment added for {client_name}"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        print(f"Error creating appointment: {e}")
        return {"success": False, "message": "Error creating appointment"}

@app.post("/admin/update-schedule")
async def update_schedule(
    start_hour: int = Form(...),
    end_hour: int = Form(...),
    db: Session = Depends(get_db),
    auth: bool = Depends(check_admin_auth)
):
    crud.update_schedule(db, start_hour, end_hour)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/toggle-schedule")
async def toggle_schedule(db: Session = Depends(get_db), auth: bool = Depends(check_admin_auth)):
    crud.toggle_schedule(db)
    return RedirectResponse(url="/admin/staff", status_code=303)

@app.post("/admin/cleanup")
async def cleanup_daily(db: Session = Depends(get_db)):
    cleaned = crud.cleanup_daily_and_save_revenue(db)
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.get("/admin/revenue", response_class=HTMLResponse)
async def revenue_reports(request: Request, view: str = "monthly", date: str = None, location: int = None, revenue_logged_in: str = Cookie(None), db: Session = Depends(get_db)):
    # Only ask for password if not logged in AND it's the main revenue access (no view parameter from URL)
    if revenue_logged_in != "true" and not request.url.query:
        return templates.TemplateResponse("revenue_login.html", {"request": request})
    
    if location is None:
        location = int(os.environ.get('DEFAULT_LOCATION', 1))
    
    if view == "daily":
        revenue_data = crud.get_daily_revenue(db, date, location)
        template = "daily_revenue.html"
    elif view == "weekly":
        revenue_data = crud.get_weekly_revenue(db, date, location)
        template = "weekly_revenue.html"
    else:
        revenue_data = crud.get_monthly_revenue(db, location_id=location)
        template = "monthly_revenue.html"
    
    location_name = "Mallorca" if location == 1 else "Concell"
    
    return templates.TemplateResponse(template, {
        "request": request,
        "revenue_data": revenue_data,
        "current_view": view,
        "selected_date": date or datetime.now().strftime('%Y-%m-%d'),
        "location": location_name,
        "location_id": location
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

# Excel export temporarily disabled for deployment compatibility

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
        
        # Trigger dashboard refresh
        global last_booking_time
        import time
        last_booking_time = time.time()
        print(f"Appointment cancelled! Updated last_booking_time to {last_booking_time}")
        
        # Send cancellation email async
        import threading
        def send_cancel_email_async():
            try:
                send_cancellation_email(appointment.email, appointment.client_name, appointment.appointment_time, appointment.service.name)
                print(f"Cancellation email sent to {appointment.email}")
            except Exception as e:
                print(f"Cancellation email error: {e}")
        
        threading.Thread(target=send_cancel_email_async, daemon=True).start()
        
        return templates.TemplateResponse("cancel_success.html", {"request": request})
    else:
        return templates.TemplateResponse("cancel_appointment.html", {
            "request": request,
            "appointment": None,
            "cancel_token": cancel_token
        })

@app.get("/api/check-refresh")
async def check_refresh(request: Request, last_check: float = 0):
    from datetime import timezone, timedelta
    
    # Check business hours (CET timezone)
    cet = timezone(timedelta(hours=1))
    current_time = datetime.now(cet)
    current_hour = current_time.hour
    
    # Outside business hours - return inactive status
    if not (10 <= current_hour < 22):
        client_ip = request.client.host
        print(f"Refresh check from {client_ip} outside business hours ({current_hour}:00 CET) - returning inactive")
        return {"refresh_needed": False, "timestamp": 0, "business_hours": False}
    
    global last_booking_time
    refresh_needed = last_booking_time > last_check
    client_ip = request.client.host
    print(f"Refresh check from {client_ip}: last_booking={last_booking_time}, last_check={last_check}, refresh_needed={refresh_needed}")
    return {"refresh_needed": refresh_needed, "timestamp": last_booking_time, "business_hours": True}

@app.get("/export-data")
async def export_data(db: Session = Depends(get_db)):
    barbers = db.query(models.Barber).all()
    services = db.query(models.Service).all()
    
    return {
        "barbers": [{"name": b.name, "active": b.active} for b in barbers],
        "services": [{"name": s.name, "description": s.description, "duration": s.duration, "price": s.price} for s in services]
    }

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)