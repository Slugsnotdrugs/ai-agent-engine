from core.database import init_db, SessionLocal, Agent, Client, Lead
from datetime import datetime
import uuid

init_db()
db = SessionLocal()

# Add a test client
client = Client(
    id=str(uuid.uuid4()),
    name="Test Law Firm",
    email="test@lawfirm.com",
    subscription_tier="Professional",
    monthly_rate=3000.00,
    status="active"
)
db.add(client)
db.commit()

# Read it back
clients = db.query(Client).all()
for c in clients:
    print(f"Client: {c.name} | {c.subscription_tier} | ${c.monthly_rate}/mo")

db.close()
print("DB test passed.")
