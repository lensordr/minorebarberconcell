from sqlalchemy.orm import sessionmaker
import models

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=models.engine)
db = SessionLocal()

# Correct barber names
correct_names = ["Luca", "Michele", "Raffaele", "Abel", "Wendy", "Sergio"]

# Get all barbers
barbers = db.query(models.Barber).all()

# Update names if needed
for i, barber in enumerate(barbers):
    if i < len(correct_names):
        barber.name = correct_names[i]
        print(f"Updated barber {barber.id} to {correct_names[i]}")

db.commit()
db.close()
print("Barber names fixed!")