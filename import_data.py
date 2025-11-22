import requests
import json
from sqlalchemy.orm import sessionmaker
import models, crud

def import_from_render(render_url):
    try:
        # Get data from Render
        response = requests.get(f"{render_url}/export-data")
        data = response.json()
        
        # Import to local database
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=models.engine)
        db = SessionLocal()
        
        # Add barbers
        for barber_data in data["barbers"]:
            existing = db.query(models.Barber).filter(models.Barber.name == barber_data["name"]).first()
            if not existing:
                crud.create_barber(db, barber_data["name"])
        
        # Add services
        for service_data in data["services"]:
            existing = db.query(models.Service).filter(models.Service.name == service_data["name"]).first()
            if not existing:
                crud.create_service(db, service_data["name"], service_data["duration"], service_data["price"], service_data["description"])
        
        db.close()
        print("✅ Data imported successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    render_url = input("Enter your Render app URL (e.g., https://your-app.onrender.com): ").strip()
    import_from_render(render_url)