from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models

def get_barbers(db: Session):
    return db.query(models.Barber).all()

def get_active_barbers(db: Session):
    return db.query(models.Barber).filter(models.Barber.active == 1).all()

def get_active_barbers_by_location(db: Session, location_id: int):
    return db.query(models.Barber).filter(
        models.Barber.active == 1,
        models.Barber.location_id == location_id
    ).all()

def get_services(db: Session):
    return db.query(models.Service).all()

def get_services_by_location(db: Session, location_id: int):
    return db.query(models.Service).filter(models.Service.location_id == location_id).all()

def get_service_by_id(db: Session, service_id: int):
    return db.query(models.Service).filter(models.Service.id == service_id).first()

def get_barber_by_id(db: Session, barber_id: int):
    return db.query(models.Barber).filter(models.Barber.id == barber_id).first()

def create_barber(db: Session, name: str, location_id: int = 1):
    barber = models.Barber(name=name, location_id=location_id)
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber

def create_service(db: Session, name: str, duration: int, price: float, description: str = "", location_id: int = 1):
    service = models.Service(name=name, duration=duration, price=price, description=description, location_id=location_id)
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

def create_appointment(db: Session, client_name: str, email: str, phone: str, service_id: int, barber_id: int, appointment_time: str):
    appointment_dt = datetime.fromisoformat(appointment_time)
    now = datetime.now()
    
    # Calculate next available slot
    current_hour = now.hour
    current_minute = now.minute
    
    if current_minute < 30:
        next_hour = current_hour
        next_minute = 30
    else:
        next_hour = current_hour + 1
        next_minute = 0
    
    earliest_time = datetime.combine(now.date(), datetime.min.time().replace(hour=next_hour, minute=next_minute))
    
    # Check if appointment time is before the next available slot
    if appointment_dt < earliest_time:
        raise ValueError("Cannot book appointments in current or past time slots")
    
    # Get service duration
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise ValueError("Service not found")
    
    service_duration = service.duration
    appointment_end = appointment_dt + timedelta(minutes=service_duration)
    
    # Check for time conflicts with existing appointments
    existing_appointments = db.query(models.Appointment).filter(
        models.Appointment.barber_id == barber_id,
        models.Appointment.status != "cancelled"
    ).all()
    
    for existing in existing_appointments:
        existing_duration = existing.custom_duration or existing.service.duration
        existing_end = existing.appointment_time + timedelta(minutes=existing_duration)
        
        # Check if appointments overlap
        if (appointment_dt < existing_end and appointment_end > existing.appointment_time):
            raise ValueError("Time slot conflicts with existing appointment")
    
    from email_service import generate_cancel_token
    cancel_token = generate_cancel_token()
    
    appointment = models.Appointment(
        client_name=client_name,
        email=email,
        phone=phone,
        service_id=service_id,
        barber_id=barber_id,
        appointment_time=appointment_dt,
        cancel_token=cancel_token
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

def create_appointment_admin(db: Session, client_name: str, phone: str, service_id: int, barber_id: int, appointment_time: str):
    appointment_dt = datetime.fromisoformat(appointment_time)
    
    # Get service duration
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise ValueError("Service not found")
    
    service_duration = service.duration
    appointment_end = appointment_dt + timedelta(minutes=service_duration)
    
    # Check for time conflicts with existing appointments
    existing_appointments = db.query(models.Appointment).filter(
        models.Appointment.barber_id == barber_id,
        models.Appointment.status != "cancelled"
    ).all()
    
    for existing in existing_appointments:
        existing_duration = existing.custom_duration or existing.service.duration
        existing_end = existing.appointment_time + timedelta(minutes=existing_duration)
        
        # Check if appointments overlap
        if (appointment_dt < existing_end and appointment_end > existing.appointment_time):
            raise ValueError("Time slot conflicts with existing appointment")
    
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

def get_today_appointments_ordered_by_location(db: Session, location_id: int):
    today = datetime.now().date()
    return db.query(models.Appointment).join(models.Barber).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Appointment.status != "cancelled",
        models.Barber.location_id == location_id
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

def get_today_appointment_counts_by_location(db: Session, location_id: int):
    today = datetime.now().date()
    total = db.query(models.Appointment).join(models.Barber).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Barber.location_id == location_id
    ).count()
    
    completed = db.query(models.Appointment).join(models.Barber).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Appointment.status == "completed",
        models.Barber.location_id == location_id
    ).count()
    
    cancelled = db.query(models.Appointment).join(models.Barber).filter(
        models.Appointment.appointment_time >= today,
        models.Appointment.appointment_time < today + timedelta(days=1),
        models.Appointment.status == "cancelled",
        models.Barber.location_id == location_id
    ).count()
    
    return {"total": total, "completed": completed, "cancelled": cancelled}

def get_available_times_for_service(db: Session, barber_id: int, service_id: int):
    now = datetime.now()
    today = now.date()
    
    # Block Sunday bookings (weekday 6 = Sunday)
    if today.weekday() == 6:
        return []  # No times available on Sunday
    
    schedule = get_schedule(db)
    
    # Get service duration
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        return []
    
    service_duration = service.duration
    
    # If it's after business hours, show tomorrow's slots
    if now.hour >= schedule.end_hour:
        today = today + timedelta(days=1)
        start_time = datetime.combine(today, datetime.min.time().replace(hour=schedule.start_hour))
        end_time = datetime.combine(today, datetime.min.time().replace(hour=schedule.end_hour))
        earliest_time = start_time
    else:
        start_time = datetime.combine(today, datetime.min.time().replace(hour=schedule.start_hour))
        end_time = datetime.combine(today, datetime.min.time().replace(hour=schedule.end_hour))
        
        # Calculate next available slot based on current time
        current_hour = now.hour
        current_minute = now.minute
        
        if current_minute < 30:
            next_hour = current_hour
            next_minute = 30
        else:
            next_hour = current_hour + 1
            next_minute = 0
        
        # If we're before business hours, start from business hours
        if next_hour < schedule.start_hour:
            earliest_time = start_time
        else:
            earliest_time = datetime.combine(today, datetime.min.time().replace(hour=next_hour, minute=next_minute))
        
        # Client restriction: cannot book before 11 AM
        min_booking_time = datetime.combine(today, datetime.min.time().replace(hour=11, minute=0))
        if earliest_time < min_booking_time:
            earliest_time = min_booking_time
    
    # Get existing appointments for this barber today (exclude cancelled)
    existing_appointments = db.query(models.Appointment).filter(
        models.Appointment.barber_id == barber_id,
        models.Appointment.appointment_time >= start_time,
        models.Appointment.appointment_time <= end_time,
        models.Appointment.status != "cancelled"
    ).all()
    
    # Generate available slots (every 30 minutes)
    available_times = []
    current = start_time
    while current < end_time:
        if current >= earliest_time:
            # Check if service would fit before closing time
            service_end = current + timedelta(minutes=service_duration)
            if service_end <= end_time:
                # Check for conflicts with existing appointments
                has_conflict = False
                for existing in existing_appointments:
                    existing_duration = existing.custom_duration or existing.service.duration
                    existing_end = existing.appointment_time + timedelta(minutes=existing_duration)
                    
                    # Check if appointments would overlap
                    if (current < existing_end and service_end > existing.appointment_time):
                        has_conflict = True
                        break
                
                if not has_conflict:
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
        
        barber.today_revenue = sum(apt.custom_price or apt.service.price for apt in completed_appointments)
        barber.today_appointments = len(completed_appointments)
        
        # Get total scheduled appointments for today
        total_today = db.query(models.Appointment).filter(
            models.Appointment.barber_id == barber.id,
            models.Appointment.appointment_time >= today,
            models.Appointment.appointment_time < today + timedelta(days=1)
        ).count()
        
        barber.total_today_appointments = total_today
    
    return barbers

def get_barbers_with_revenue_by_location(db: Session, location_id: int):
    barbers = db.query(models.Barber).filter(models.Barber.location_id == location_id).all()
    today = datetime.now().date()
    
    for barber in barbers:
        # Get today's completed appointments
        completed_appointments = db.query(models.Appointment).filter(
            models.Appointment.barber_id == barber.id,
            models.Appointment.appointment_time >= today,
            models.Appointment.appointment_time < today + timedelta(days=1),
            models.Appointment.status == "completed"
        ).all()
        
        barber.today_revenue = sum(apt.custom_price or apt.service.price for apt in completed_appointments)
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
        
        monthly_record.revenue += appointment.custom_price or appointment.service.price
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
        
        daily_record.revenue += appointment.custom_price or appointment.service.price
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

def update_appointment_details(db: Session, appointment_id: int, time: str, price: float, duration: int):
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise ValueError("Appointment not found")
    
    # Update time (keep same date, change time)
    current_date = appointment.appointment_time.date()
    new_time = datetime.strptime(time, "%H:%M").time()
    new_datetime = datetime.combine(current_date, new_time)
    
    # Check if new time slot is available (exclude current appointment)
    existing = db.query(models.Appointment).filter(
        models.Appointment.barber_id == appointment.barber_id,
        models.Appointment.appointment_time == new_datetime,
        models.Appointment.status != "cancelled",
        models.Appointment.id != appointment_id
    ).first()
    
    if existing:
        raise ValueError("Time slot already booked")
    
    # Update appointment
    appointment.appointment_time = new_datetime
    
    # Update appointment-specific price and duration
    appointment.custom_price = price
    appointment.custom_duration = duration
    
    db.commit()
    db.refresh(appointment)
    return appointment

def delete_barber(db: Session, barber_id: int):
    try:
        # First delete all revenue records for this barber
        db.query(models.MonthlyRevenue).filter(models.MonthlyRevenue.barber_id == barber_id).delete()
        db.query(models.DailyRevenue).filter(models.DailyRevenue.barber_id == barber_id).delete()
        
        # Then delete all appointments for this barber
        db.query(models.Appointment).filter(models.Appointment.barber_id == barber_id).delete()
        
        # Finally delete the barber
        barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
        if barber:
            db.delete(barber)
            db.commit()
        return barber
    except Exception as e:
        db.rollback()
        print(f"Error deleting barber: {e}")
        raise e

def toggle_barber_status(db: Session, barber_id: int):
    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if barber:
        barber.active = 1 - barber.active  # Toggle between 0 and 1
        db.commit()
        db.refresh(barber)
    return barber

def update_barber_name(db: Session, barber_id: int, new_name: str):
    barber = db.query(models.Barber).filter(models.Barber.id == barber_id).first()
    if barber:
        barber.name = new_name
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

def get_monthly_revenue(db: Session, year: int = None, month: int = None, location_id: int = None):
    if not year or not month:
        today = datetime.now().date()
        year = today.year
        month = today.month
    
    query = db.query(models.MonthlyRevenue).filter(
        models.MonthlyRevenue.year == year,
        models.MonthlyRevenue.month == month
    )
    
    if location_id:
        query = query.join(models.Barber).filter(models.Barber.location_id == location_id)
    
    records = query.all()
    
    total_revenue = sum(record.revenue for record in records)
    total_appointments = sum(record.appointments_count for record in records)
    
    return {
        "records": records,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments
    }

def get_daily_revenue(db: Session, date: str = None, location_id: int = None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    query = db.query(models.DailyRevenue).filter(
        models.DailyRevenue.date == date
    )
    
    if location_id:
        query = query.join(models.Barber).filter(models.Barber.location_id == location_id)
    
    records = query.all()
    
    total_revenue = sum(record.revenue for record in records)
    total_appointments = sum(record.appointments_count for record in records)
    
    return {
        "records": records,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "date": date
    }

def get_barber_with_least_appointments(db: Session, service_id: int, appointment_time: str, location_id: int = None):
    """Find active barber with least appointments for the day (excludes Luca and Raffa from random)"""
    appointment_dt = datetime.fromisoformat(appointment_time)
    today = appointment_dt.date()
    
    if location_id:
        active_barbers = get_active_barbers_by_location(db, location_id)
    else:
        active_barbers = get_active_barbers(db)
    
    # Exclude Luca and Raffa from random selection
    excluded_names = ['Luca', 'Raffa']
    eligible_barbers = [b for b in active_barbers if b.name not in excluded_names]
    
    barber_counts = []
    
    for barber in eligible_barbers:
        # Count today's appointments for this barber
        count = db.query(models.Appointment).filter(
            models.Appointment.barber_id == barber.id,
            models.Appointment.appointment_time >= today,
            models.Appointment.appointment_time < today + timedelta(days=1),
            models.Appointment.status != "cancelled"
        ).count()
        
        # Check if this barber has availability for the requested time
        available_times = get_available_times_for_service(db, barber.id, service_id)
        requested_time = appointment_dt.strftime("%H:%M")
        
        if requested_time in available_times:
            barber_counts.append((barber.id, count))
    
    if not barber_counts:
        return None
    
    # Return barber with least appointments
    return min(barber_counts, key=lambda x: x[1])[0]

def get_weekly_revenue(db: Session, date: str = None, location_id: int = None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Get start of week (Monday)
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get all daily records for the week
    query = db.query(models.DailyRevenue).filter(
        models.DailyRevenue.date >= start_of_week.strftime('%Y-%m-%d'),
        models.DailyRevenue.date <= end_of_week.strftime('%Y-%m-%d')
    )
    
    if location_id:
        query = query.join(models.Barber).filter(models.Barber.location_id == location_id)
    
    records = query.all()
    
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