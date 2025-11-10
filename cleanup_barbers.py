from sqlalchemy.orm import sessionmaker
import models

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=models.engine)
db = SessionLocal()

# Keep only the correct 6 barbers
correct_barbers = ["Luca", "Michele", "Raffaele", "Abel", "Wendy", "Sergio"]

# Delete extra barbers
extra_barbers = db.query(models.Barber).filter(~models.Barber.name.in_(correct_barbers)).all()
for barber in extra_barbers:
    print(f"Deleting barber: {barber.name}")
    db.delete(barber)

db.commit()
db.close()
print("Extra barbers removed!")