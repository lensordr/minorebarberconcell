from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models

def get_barbers(db: Session):
    return db.query(models.Barber).all()

def get_active_barbers(db: Session):
    return db.query(models.Barber).filter(models.Barber.active == 1).all()

def get_services(db: Session):
    return db.query(models.Service).all()

def create_barber(db: Session, name: str):
    barber = models.Barber(name=name)
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber

def create_service(db: Session, name: str, duration: int, price: float, description: str = ""):
    service = models.Service(name=name, duration=duration, price=price, description=description)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

def update_service(db: Session, service_id: int, name: str, duration: int, price: float, description: str):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if service:
        service.name = name
        service.duration = duration
        service.price = price
        service.description = description
        db.commit()
        db.refresh(service)
    return service

def delete_service(db: Session, service_id: int):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if service:
        db.delete(service)
        db.commit()
    return service

def create_appointment(db: Session, client_name: str, phone: str, service_id: int, barber_id: int, appointment_time: str):
    appointment_dt = datetime.fromisoformat(appointment_time)
    
    # Check if slot is already taken
    existing = db.query(models.Appointment).filter(
        models.Appointment.barber_id == barber_id,
        models.Appointment.appointment_time == appointment_dt,
        models.Appointment.status != "cancelled"
    ).first()
    
    if existing:
        raise ValueError("Time slot already booked")
    
    appointment = models.Appointment(
        client_name=client_name,
        phone=phone,
        service_id=service_id,
        barber_id=barber_id,
        appointment_time=appointment_dt
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

def get_today_appointments_ordered(db: Session):
    today = datetime.now().date()
    return db.query(models.Appointment).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Appointment.status != "cancelled"
    ).order_by(models.Appointment.appointment_time).all()

def get_today_appointment_counts(db: Session):
    today = datetime.now().date()
    total = db.query(models.Appointment).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1)
    ).count()
    
    completed = db.query(models.Appointment).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Appointment.status == "completed"
    ).count()
    
    cancelled = db.query(models.Appointment).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Appointment.status == "cancelled"
    ).count()
    
    return {"total": total, "completed": completed, "cancelled": cancelled}

def get_available_times(db: Session, barber_id: int):
    now = datetime.now()
    today = now.date()
    schedule = get_schedule(db)
    
    start_time = datetime.combine(today, datetime.min.time().replace(hour=schedule.start_hour))
    end_time = datetime.combine(today, datetime.min.time().replace(hour=schedule.end_hour))
    
    # Get existing appointments for this barber today (exclude cancelled)
    existing = db.query(models.Appointment).filter(
        models.Appointment.barber_id == barber_id,
        models.Appointment.appointment_time >= start_time,
        models.Appointment.appointment_time <= end_time,
        models.Appointment.status != "cancelled"
    ).all()
    
    # Generate available slots (every 30 minutes)
    available_times = []
    current = start_time
    while current < end_time:
        # Only show times that are in the future (at least 30 minutes from now)
        if current > now + timedelta(minutes=30):
            is_available = True
            for appointment in existing:
                if appointment.appointment_time == current:
                    is_available = False
                    break
            
            if is_available:
                available_times.append(current.strftime("%H:%M"))
        
        current += timedelta(minutes=30)
    
    return available_times

def get_barber_revenue(db: Session, barber_id: int, date: datetime.date = None):
    if date is None:
        date = datetime.now().date()
    
    appointments = db.query(models.Appointment).filter(
        models.Appointment.barber_id == barber_id,
        models.Appointment.appointment_time >= date,
        models.Appointment.appointment_time < date + timedelta(days=1),
        models.Appointment.status == "completed"
    ).all()
    
    total = sum(appointment.service.price for appointment in appointments)
    return total

def get_barbers_with_revenue(db: Session):
    barbers = get_barbers(db)
    today = datetime.now().date()
    
    for barber in barbers:
        # Get today's completed appointments
        completed_appointments = db.query(models.Appointment).filter(
            models.Appointment.barber_id == barber.id,
            models.Appointment.appointment_time >= today,
            models.Appointment.appointment_time < today + timedelta(days=1),
            models.Appointment.status == "completed"
        ).all()
        
        barber.today_revenue = sum(apt.service.price for apt in completed_appointments)
        barber.today_appointments = len(completed_appointments)
        
        # Get total scheduled appointments for today
        total_today = db.query(models.Appointment).filter(
            models.Appointment.barber_id == barber.id,
            models.Appointment.appointment_time >= today,
            models.Appointment.appointment_time < today + timedelta(days=1)
        ).count()
        
        barber.total_today_appointments = total_today
    
    return barbers

def checkout_appointment(db: Session, appointment_id: int):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if appointment:
        appointment.status = "completed"
        
        # Save to monthly revenue immediately
        today = datetime.now().date()
        monthly_record = db.query(models.MonthlyRevenue).filter(
            models.MonthlyRevenue.barber_id == appointment.barber_id,
            models.MonthlyRevenue.year == today.year,
            models.MonthlyRevenue.month == today.month
        ).first()
        
        if not monthly_record:
            monthly_record = models.MonthlyRevenue(
                barber_id=appointment.barber_id,
                year=today.year,
                month=today.month,
                revenue=0,
                appointments_count=0
            )
            db.add(monthly_record)
        
        monthly_record.revenue += appointment.service.price
        monthly_record.appointments_count += 1
        
        # Save to daily revenue
        date_str = today.strftime('%Y-%m-%d')
        daily_record = db.query(models.DailyRevenue).filter(
            models.DailyRevenue.barber_id == appointment.barber_id,
            models.DailyRevenue.date == date_str
        ).first()
        
        if not daily_record:
            daily_record = models.DailyRevenue(
                barber_id=appointment.barber_id,
                date=date_str,
                revenue=0,
                appointments_count=0
            )
            db.add(daily_record)
        
        daily_record.revenue += appointment.service.price
        daily_record.appointments_count += 1
        
        db.commit()
        db.refresh(appointment)
    return appointment

def cancel_appointment(db: Session, appointment_id: int):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if appointment:
        appointment.status = "cancelled"
        db.commit()
        db.refresh(appointment)
    return appointment

def delete_barber(db: Session, barber_id: int):
    # First delete all appointments for this barber
    db.query(models.Appointment).filter(models.Appointment.barber_id == barber_id).delete()
    # Then delete the barber
    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if barber:
        db.delete(barber)
        db.commit()
    return barber

def toggle_barber_status(db: Session, barber_id: int):
    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if barber:
        barber.active = 1 - barber.active  # Toggle between 0 and 1
        db.commit()
        db.refresh(barber)
    return barber

def get_schedule(db: Session):
    schedule = db.query(models.Schedule).first()
    if not schedule:
        schedule = models.Schedule()
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
    return schedule

def update_schedule(db: Session, start_hour: int, end_hour: int):
    schedule = get_schedule(db)
    schedule.start_hour = start_hour
    schedule.end_hour = end_hour
    db.commit()
    db.refresh(schedule)
    return schedule

def cleanup_daily_and_save_revenue(db: Session):
    today = datetime.now().date()
    
    # Delete all appointments older than today (revenue already saved live)
    deleted_count = db.query(models.Appointment).filter(
        models.Appointment.appointment_time < today
    ).delete()
    
    db.commit()
    return deleted_count

def get_monthly_revenue(db: Session, year: int = None, month: int = None):
    if not year or not month:
        today = datetime.now().date()
        year = today.year
        month = today.month
    
    records = db.query(models.MonthlyRevenue).filter(
        models.MonthlyRevenue.year == year,
        models.MonthlyRevenue.month == month
    ).all()
    
    total_revenue = sum(record.revenue for record in records)
    total_appointments = sum(record.appointments_count for record in records)
    
    return {
        "records": records,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments
    }

def get_daily_revenue(db: Session, date: str = None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    records = db.query(models.DailyRevenue).filter(
        models.DailyRevenue.date == date
    ).all()
    
    total_revenue = sum(record.revenue for record in records)
    total_appointments = sum(record.appointments_count for record in records)
    
    return {
        "records": records,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "date": date
    }

def get_weekly_revenue(db: Session, date: str = None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Get start of week (Monday)
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get all daily records for the week
    records = db.query(models.DailyRevenue).filter(
        models.DailyRevenue.date >= start_of_week.strftime('%Y-%m-%d'),
        models.DailyRevenue.date <= end_of_week.strftime('%Y-%m-%d')
    ).all()
    
    # Group by barber
    barber_totals = {}
    for record in records:
        if record.barber_id not in barber_totals:
            barber_totals[record.barber_id] = {
                "barber": record.barber,
                "revenue": 0,
                "appointments_count": 0
            }
        barber_totals[record.barber_id]["revenue"] += record.revenue
        barber_totals[record.barber_id]["appointments_count"] += record.appointments_count
    
    weekly_records = list(barber_totals.values())
    total_revenue = sum(r["revenue"] for r in weekly_records)
    total_appointments = sum(r["appointments_count"] for r in weekly_records)
    
    return {
        "records": weekly_records,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "week_start": start_of_week.strftime('%Y-%m-%d'),
        "week_end": end_of_week.strftime('%Y-%m-%d')
    }