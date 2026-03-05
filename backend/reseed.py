import os
import sys

try:
    if os.path.exists("test_shieldops.db"):
        os.remove("test_shieldops.db")
    if os.path.exists("shieldops.db"):
        os.remove("shieldops.db")
        print("Deleted existing shieldops.db")
except Exception as e:
    print(f"Failed to delete databases: {e}")
    sys.exit(1)

from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
print("Created new tables via SQLAlchemy")

from database import SessionLocal
import seed
import seed_test_data

db = SessionLocal()
try:
    seed.seed_tools(db)
    print("Seeded tools")
finally:
    db.close()

seed_test_data.seed_test_data()
print("Database re-seeded successfully.")
