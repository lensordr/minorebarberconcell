from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models, crud
from database import get_db
import json

app = FastAPI()

@app.get("/export-data")
def export_data(db: Session = Depends(get_db)):
    # Export all data
    barbers = db.query(models.Barber).all()
    services = db.query(models.Service).all()
    
    data = {
        "barbers": [{"name": b.name, "active": b.active} for b in barbers],
        "services": [{"name": s.name, "description": s.description, "duration": s.duration, "price": s.price} for s in services]
    }
    
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)