import time
import json
from datetime import datetime

TRIGGER_FILE = "last_appointment.json"

def trigger_dashboard_refresh():
    """Update timestamp to signal dashboard refresh"""
    current_time = datetime.now().timestamp()
    with open(TRIGGER_FILE, 'w') as f:
        json.dump({"timestamp": current_time}, f)
    print(f"Dashboard refresh triggered at {current_time}")

def get_last_update():
    """Get last update timestamp"""
    try:
        with open(TRIGGER_FILE, 'r') as f:
            data = json.load(f)
            return data.get("timestamp", 0)
    except:
        return 0