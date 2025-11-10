import requests
import time
from datetime import datetime

def ping_app():
    """Ping the app to keep it alive during business hours"""
    url = "https://minore-barbershop.onrender.com/"
    
    while True:
        now = datetime.now()
        # Keep alive during business hours (9 AM - 8 PM)
        if 9 <= now.hour <= 20:
            try:
                response = requests.get(url, timeout=10)
                print(f"Ping at {now}: Status {response.status_code}")
            except Exception as e:
                print(f"Ping failed at {now}: {e}")
        
        # Wait 10 minutes before next ping
        time.sleep(600)

if __name__ == "__main__":
    ping_app()