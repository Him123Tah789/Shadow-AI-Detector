import os
import random
from datetime import datetime, timedelta
from database import SessionLocal, engine
from models import Organization, Admin, Policy, UsageEvent, ToolCatalog, Base

def seed_test_data():
    db = SessionLocal()
    try:
        # Get or create an organization
        org = db.query(Organization).first()
        if not org:
            org = Organization(name="Test Organization", token="test_org_token_123")
            db.add(org)
            db.commit()
            db.refresh(org)
            
            # create an admin
            admin = Admin(
                org_id=org.id,
                email="admin@test.com",
                password_hash="test",  # Not a real hash, just for linking
                role="admin"
            )
            db.add(admin)
            db.commit()
        
        # Tools
        chatgpt = db.query(ToolCatalog).filter(ToolCatalog.domain == "chat.openai.com").first()
        chatgpt2 = db.query(ToolCatalog).filter(ToolCatalog.domain == "chatgpt.com").first()
        claude = db.query(ToolCatalog).filter(ToolCatalog.domain == "claude.ai").first()
        gemini = db.query(ToolCatalog).filter(ToolCatalog.domain == "gemini.google.com").first()
        
        if not all([chatgpt, chatgpt2, claude, gemini]):
            print("Running seed_tools.py to populate catalog first...")
            from seed import seed_tools
            seed_tools(db)
            chatgpt = db.query(ToolCatalog).filter(ToolCatalog.domain == "chat.openai.com").first()
            chatgpt2 = db.query(ToolCatalog).filter(ToolCatalog.domain == "chatgpt.com").first()
            claude = db.query(ToolCatalog).filter(ToolCatalog.domain == "claude.ai").first()
            gemini = db.query(ToolCatalog).filter(ToolCatalog.domain == "gemini.google.com").first()

        # Clear existing policies and events for a clean slate
        db.query(Policy).filter(Policy.org_id == org.id).delete()
        db.query(UsageEvent).filter(UsageEvent.org_id == org.id).delete()
        db.commit()

        # Insert 4 Policies (as requested + the extra chatgpt.com domain alias)
        policies = [
            Policy(org_id=org.id, tool_id=chatgpt.id, action="allow"),
            Policy(org_id=org.id, tool_id=chatgpt2.id, action="allow"),
            Policy(org_id=org.id, tool_id=claude.id, action="warn", alternative_tool_id=chatgpt.id),
            Policy(org_id=org.id, tool_id=gemini.id, action="block", alternative_tool_id=chatgpt.id),
        ]
        db.add_all(policies)
        db.commit()
        print("✅ Added 4 Policies (Allow chat.openai.com/chatgpt.com, Warn claude.ai, Block gemini.google.com)")

        # Insert 50 Events across the last 30 days
        events = []
        for i in range(50):
            action = random.choice(["allow", "allow", "warn", "block"])
            domain = {
                "allow": "chat.openai.com",
                "warn": "claude.ai",
                "block": "gemini.google.com"
            }[action]
            
            # spread over last 30 days
            days_ago = random.randint(0, 30)
            events.append(UsageEvent(
                org_id=org.id,
                domain=domain,
                user_hash=f"user_{random.randint(1, 5)}",
                policy_action=action,
                timestamp=datetime.utcnow() - timedelta(days=days_ago)
            ))
        
        db.add_all(events)
        db.commit()
        print(f"✅ Added {len(events)} synthetic Usage Events to light up the dashboard")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding test data into DB...")
    seed_test_data()
    print("Done! Refresh the dashboard now.")
