from fastapi import FastAPI, Request, Depends, HTTPException, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models, crud
from database import get_db
import uvicorn
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

def check_admin_auth(request: Request, admin_logged_in: str = Cookie(None)):
    if admin_logged_in != "true":
        return RedirectResponse(url="/admin/login", status_code=303)
    return True

app = FastAPI(title="MINORE BARBERSHOP")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create tables
models.Base.metadata.create_all(bind=models.engine)

# Scheduler for automatic cleanup
scheduler = AsyncIOScheduler()

async def auto_cleanup():
    """Automatic daily cleanup at 22:00"""
    db = next(get_db())
    try:
        cleaned = crud.cleanup_daily_and_save_revenue(db)
        print(f"Auto cleanup completed: {cleaned} appointments processed")
    except Exception as e:
        print(f"Auto cleanup error: {e}") 
    finally:
        db.close()

# Schedule cleanup every day at 22:00
scheduler.add_job(
    auto_cleanup,
    CronTrigger(hour=22, minute=0),
    id='daily_cleanup',
    replace_existing=True
)

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    print("Scheduler started - Auto cleanup at 22:00 daily")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

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
    phone: str = Form(...),
    service_id: int = Form(...),
    barber_id: int = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        appointment = crud.create_appointment(db, client_name, phone, service_id, barber_id, appointment_time)
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
    appointments = crud.get_today_appointments_ordered(db)
    barbers = crud.get_barbers_with_revenue(db)
    services = crud.get_services(db)
    schedule = crud.get_schedule(db)
    counts = crud.get_today_appointment_counts(db)
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "appointments": appointments,
        "barbers": crud.get_active_barbers(db),  # Only active barbers for walk-in form
        "all_barbers": barbers,  # All barbers for grid display
        "services": services,
        "schedule": schedule,
        "counts": counts,
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

@app.post("/admin/add-appointment")
async def add_manual_appointment(
    client_name: str = Form(...),
    phone: str = Form(...),
    service_id: int = Form(...),
    barber_id: int = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        crud.create_appointment(db, client_name, phone, service_id, barber_id, appointment_time)
    except ValueError:
        pass  # Time slot already taken
    return RedirectResponse(url="/admin/dashboard", status_code=303)

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
async def revenue_reports(request: Request, view: str = "monthly", date: str = None, db: Session = Depends(get_db)):
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

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_logged_in")
    return response

@app.get("/api/available-times/{barber_id}")
async def get_available_times(barber_id: int, db: Session = Depends(get_db)):
    return crud.get_available_times(db, barber_id)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)