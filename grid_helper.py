from datetime import datetime, timedelta

def create_appointment_grid(db, appointments, schedule, location_id=None):
    """Create a grid structure showing which time slots are occupied by appointments"""
    import crud
    
    grid = {}
    
    # Generate all time slots
    hours = []
    for h in range(schedule.start_hour, schedule.end_hour):
        hours.append(f"{h:02d}:00")
        hours.append(f"{h:02d}:30")
    
    # Initialize grid for each barber (include inactive to prevent ID mismatches)
    if location_id:
        all_barbers = crud.get_barbers_with_revenue_by_location(db, location_id)
    else:
        all_barbers = crud.get_barbers(db)
    for barber in all_barbers:
        grid[barber.id] = {}
        for hour in hours:
            grid[barber.id][hour] = {
                "type": "empty",
                "appointment": None,
                "is_start": False,
                "span_rows": 1
            }
    
    # Fill grid with appointments
    for appointment in appointments:
        if appointment.status == "cancelled":
            continue
            
        barber_id = appointment.barber_id
        start_time = appointment.appointment_time.strftime("%H:%M")
        duration = appointment.custom_duration or appointment.service.duration
        slots_needed = (duration + 29) // 30  # Round up to nearest 30min slot
        
        if barber_id in grid and start_time in grid[barber_id]:
            print(f"Processing appointment {appointment.id} at {start_time}, duration {duration}min, slots_needed {slots_needed}")
            # Mark the starting slot
            grid[barber_id][start_time] = {
                "type": "appointment",
                "appointment": appointment,
                "is_start": True,
                "span_rows": slots_needed
            }
            
            # Mark continuation slots
            start_idx = hours.index(start_time)
            for i in range(1, slots_needed):
                if start_idx + i < len(hours):
                    next_slot = hours[start_idx + i]
                    grid[barber_id][next_slot] = {
                        "type": "continuation",
                        "appointment": appointment,
                        "is_start": False,
                        "span_rows": 1
                    }
                    print(f"Marking {next_slot} as continuation for appointment {appointment.id}")
    
    return {"grid": grid, "hours": hours}