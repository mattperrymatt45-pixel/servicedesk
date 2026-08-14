import sys
import os
from datetime import datetime, timedelta, timezone

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models import KBArticle, Ticket, TicketActivity
from scripts.import_dataset import import_huggingface_dataset


def seed_database():
    """
    Seed database by downloading Knowledge Base dataset from Hugging Face
    and populating sample support tickets.
    """
    print("🌱 Initializing Database Seeder...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        kb_count = db.query(KBArticle).count()

        # 1. Import Knowledge Base exclusively from Hugging Face dataset
        if kb_count == 0:
            print("🚀 Importing Knowledge Base from Hugging Face dataset (mindweave/help-desk-tickets)...")
            import_huggingface_dataset(target_count=100, clear_existing=False)
        else:
            print(f"ℹ️ Knowledge Base already contains {kb_count} articles.")

        ticket_count = db.query(Ticket).count()
        if ticket_count > 0:
            print(f"ℹ️ Database already contains {ticket_count} support tickets. Skipping ticket seed.")
            return

        # 2. Seed 12 Sample Support Tickets
        print("🚀 Seeding Sample Support Tickets...")
        now = datetime.now(timezone.utc)

        tickets_data = [
            {
                "title": "Cannot connect to VPN from home office Wi-Fi",
                "description": "I'm trying to connect to GlobalProtect VPN from home to access internal Git repos. The client gets stuck at 'Connecting' and then gives gateway timeout error.",
                "status": "Open",
                "priority": "High",
                "category": "Network & VPN",
                "created_at": now - timedelta(hours=2)
            },
            {
                "title": "Domain account locked out after password change",
                "description": "Changed my password on the web portal this morning. Now my laptop account is locked and my phone keeps failing MFA.",
                "status": "In Progress",
                "priority": "Urgent",
                "category": "Access Management",
                "created_at": now - timedelta(hours=5)
            },
            {
                "title": "3rd Floor Finance HP Printer displaying Offline status",
                "description": "The main HP LaserJet printer on the 3rd floor Finance wing shows offline for all team members. Several urgent invoices are stuck in queue.",
                "status": "Open",
                "priority": "Medium",
                "category": "Printers & Devices",
                "created_at": now - timedelta(hours=8)
            },
            {
                "title": "Outlook email client stuck on 'Updating Inbox'",
                "description": "My Microsoft Outlook app on Windows 11 stopped receiving new emails since 9 AM today. New emails show up on Web Outlook fine.",
                "status": "In Progress",
                "priority": "Medium",
                "category": "Email & Collaboration",
                "created_at": now - timedelta(hours=12)
            },
            {
                "title": "Laptop extremely slow with 100% CPU usage in Task Manager",
                "description": "Dell Latitude laptop fan is making loud noise and opening any application takes minutes. Task Manager shows CPU at 100% constantly.",
                "status": "Open",
                "priority": "High",
                "category": "Laptop / Endpoint",
                "created_at": now - timedelta(days=1)
            },
            {
                "title": "Blue Screen crash with KMODE_EXCEPTION error on boot",
                "description": "Engineering workstation crashed with BSOD stop code KMODE_EXCEPTION_NOT_HANDLED after yesterday's automated Windows update.",
                "status": "Open",
                "priority": "Urgent",
                "category": "Laptop / Endpoint",
                "created_at": now - timedelta(days=1, hours=4)
            },
            {
                "title": "Wi-Fi connected but showing 'No Internet Access' in Conference Room B",
                "description": "During team meeting in Conf Room B, laptop connected to Corp_Guest Wi-Fi but displays no internet access symbol.",
                "status": "Resolved",
                "priority": "Low",
                "category": "Network & VPN",
                "final_resolution": "Flushed DNS cache and renewed DHCP lease on laptop. Reconnected to Corp_Secure SSID.",
                "created_at": now - timedelta(days=2)
            },
            {
                "title": "Request for Docker Desktop software installation and admin rights",
                "description": "New developer joining backend team needs Docker Desktop and VS Code extension installed for local microservice development.",
                "status": "Open",
                "priority": "Medium",
                "category": "Access Management",
                "created_at": now - timedelta(days=2, hours=6)
            },
            {
                "title": "Microsoft Teams microphone grayed out during customer call",
                "description": "When joining external client call in Teams, my headset microphone is not detected and audio settings show no input devices found.",
                "status": "In Progress",
                "priority": "High",
                "category": "Email & Collaboration",
                "created_at": now - timedelta(days=3)
            },
            {
                "title": "Access Denied when trying to open \\\\server\\Marketing-Shared folder",
                "description": "Transferred to Marketing department this week but cannot open shared network drive. Getting Windows access denied error message.",
                "status": "Open",
                "priority": "Medium",
                "category": "Access Management",
                "created_at": now - timedelta(days=3, hours=10)
            },
            {
                "title": "C: Drive low disk space red warning (Only 500 MB remaining)",
                "description": "Received popup stating C: drive is almost full. Cannot save new project files or update software applications.",
                "status": "Resolved",
                "priority": "Medium",
                "category": "Laptop / Endpoint",
                "final_resolution": "Ran Windows Disk Cleanup and removed 18 GB of Windows Update backup files.",
                "created_at": now - timedelta(days=4)
            },
            {
                "title": "SSL Certificate warning on internal HR payroll portal",
                "description": "Chrome displays NET::ERR_CERT_DATE_INVALID warning when attempting to log into https://payroll.internal.corp.",
                "status": "Resolved",
                "priority": "Low",
                "category": "Security",
                "final_resolution": "Re-installed corporate root certificate into Trusted Root Store.",
                "created_at": now - timedelta(days=5)
            }
        ]

        for ticket_dict in tickets_data:
            t = Ticket(
                title=ticket_dict["title"],
                description=ticket_dict["description"],
                status=ticket_dict["status"],
                priority=ticket_dict["priority"],
                category=ticket_dict["category"],
                final_resolution=ticket_dict.get("final_resolution"),
                created_at=ticket_dict["created_at"],
                updated_at=ticket_dict["created_at"]
            )
            db.add(t)
            db.flush()

            # Add initial activity log
            activity = TicketActivity(
                ticket_id=t.id,
                activity_type="CREATED",
                notes=f"Ticket created with priority '{t.priority}' in category '{t.category}'",
                created_at=t.created_at
            )
            db.add(activity)

        db.commit()
        print(f"✅ Successfully seeded {len(tickets_data)} support tickets with activity logs!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
