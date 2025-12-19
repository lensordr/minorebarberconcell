from datetime import datetime, timedelta

def create_appointment_grid(db, appointments, schedule, location_id=None):
    """Optimized grid creation - minimal database calls"""
    import crud
    
    # Generate time slots once
    hours = []
    for h in range(schedule.start_hour, schedule.end_hour):
        hours.append(f"{h:02d}:00")
        hours.append(f"{h:02d}:30")
    
    # Get barbers with single query (already optimized)
    if location_id:
        all_barbers = crud.get_barbers_with_revenue_by_location(db, location_id)
    else:
        all_barbers = crud.get_barbers(db)
    
    # Pre-create empty grid structure
    empty_slot = {"type": "empty", "appointment": None, "is_start": False, "span_rows": 1}
    grid = {barber.id: {hour: empty_slot.copy() for hour in hours} for barber in all_barbers}
    
    # Create hour index lookup for faster processing
    hour_index = {hour: idx for idx, hour in enumerate(hours)}
    
    # Fill grid with appointments (optimized loop)
    for appointment in appointments:
        if appointment.status == "cancelled":
            continue
            
        barber_id = appointment.barber_id
        start_time = appointment.appointment_time.strftime("%H:%M")
        
        if barber_id not in grid or start_time not in hour_index:
            continue
            
        duration = appointment.custom_duration or appointment.service.duration
        slots_needed = (duration + 29) // 30
        
        # Mark starting slot
        grid[barber_id][start_time] = {
            "type": "appointment",
            "appointment": appointment,
            "is_start": True,
            "span_rows": slots_needed
        }
        
        # Mark continuation slots efficiently
        start_idx = hour_index[start_time]
        for i in range(1, min(slots_needed, len(hours) - start_idx)):
            next_slot = hours[start_idx + i]
            grid[barber_id][next_slot] = {
                "type": "continuation",
                "appointment": appointment,
                "is_start": False,
                "span_rows": 1
            }
    
    return {"grid": grid, "hours": hours}