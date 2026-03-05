import datetime
import secrets

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Organization, Admin, ToolCatalog, Policy, UsageEvent

def main():
    db: Session = SessionLocal()
    
    try:
        # Get or create an organization
        org = db.query(Organization).first()
        if not org:
            org = Organization(name="Test Org", token=secrets.token_urlsafe(32))
            db.add(org)
            db.flush()
            
            admin = Admin(
                org_id=org.id,
                email="admin@example.com",
                password_hash="fakehash",
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("Created Organization and Admin")
            
        print(f"Using Organization: {org.name} (ID: {org.id})")
        
        # Tools to map
        # ChatGPT: chat.openai.com and chatgpt.com
        # Claude: claude.ai
        # Gemini: gemini.google.com

        tool_chat_openai = db.query(ToolCatalog).filter_by(domain="chat.openai.com").first()
        tool_chatgpt = db.query(ToolCatalog).filter_by(domain="chatgpt.com").first()
        tool_claude = db.query(ToolCatalog).filter_by(domain="claude.ai").first()
        tool_gemini = db.query(ToolCatalog).filter_by(domain="gemini.google.com").first()

        policies = [
            (tool_chat_openai.id, "allow"),
            (tool_chatgpt.id, "allow"),
            (tool_claude.id, "warn"),
            (tool_gemini.id, "block")
        ]
        
        # Insert Policies
        for t_id, action in policies:
            existing = db.query(Policy).filter_by(org_id=org.id, tool_id=t_id).first()
            if existing:
                existing.action = action
                print(f"Updated policy for tool ID {t_id} to {action}")
            else:
                db.add(Policy(org_id=org.id, tool_id=t_id, action=action))
                print(f"Added policy for tool ID {t_id} to {action}")
                
        # Insert an event
        event_time = datetime.datetime.utcnow()
        new_event = UsageEvent(
            org_id=org.id,
            domain="chat.openai.com",
            user_hash="test_user_01",
            policy_action="allowed",
            timestamp=event_time
        )
        db.add(new_event)
        
        # Add another event for stats
        db.add(UsageEvent(
            org_id=org.id,
            domain="claude.ai",
            user_hash="test_user_02",
            policy_action="warn",
            timestamp=event_time
        ))
        
        db.add(UsageEvent(
            org_id=org.id,
            domain="gemini.google.com",
            user_hash="test_user_03",
            policy_action="block",
            timestamp=event_time
        ))

        db.commit()
        print("Inserted policies and test events successfully.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
