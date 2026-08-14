import sys
import os
import re
import logging
from typing import Set, Tuple, List, Dict, Any

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import KBArticle

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("dataset_import")


CATEGORY_NORMALIZATION = {
    "access management": "Access Management",
    "identity": "Access Management",
    "laptop / endpoint": "Laptop / Endpoint",
    "endpoint": "Laptop / Endpoint",
    "network & vpn": "Network & VPN",
    "network": "Network & VPN",
    "vpn": "Network & VPN",
    "email & collaboration": "Email & Collaboration",
    "saas": "Email & Collaboration",
    "mail": "Email & Collaboration",
    "erp / wms": "ERP / WMS",
    "business-apps": "ERP / WMS",
    "printers & devices": "Printers & Devices",
    "peripherals": "Printers & Devices",
    "security": "Security",
    "telephony": "Telephony",
    "voice": "Telephony"
}


def normalize_category(cat_str: str) -> str:
    """Normalize raw dataset category names into standardized enterprise categories."""
    if not cat_str:
        return "General IT"
    clean = cat_str.strip().lower()
    return CATEGORY_NORMALIZATION.get(clean, cat_str.strip().title())


def import_huggingface_dataset(target_count: int = 100, clear_existing: bool = True) -> Dict[str, int]:
    """
    Downloads and inspects the Hugging Face help-desk-tickets dataset, cleans the records,
    maps them to the KBArticle model, and inserts exactly 100 high-quality unique records into SQLite.
    
    Idempotent: prevents duplicate insertions if executed multiple times.
    """
    logger.info("====================================================")
    logger.info("Starting Hugging Face Dataset Import (mindweave/help-desk-tickets)")
    logger.info("====================================================")

    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Please install via 'pip install datasets'.")
        sys.exit(1)

    # 1. Download Dataset
    logger.info("Downloading dataset splits from Hugging Face...")
    try:
        cats_ds = load_dataset('mindweave/help-desk-tickets', 'categories')['train']
        tickets_ds = load_dataset('mindweave/help-desk-tickets', 'tickets')['train']
        comments_ds = load_dataset('mindweave/help-desk-tickets', 'comments')['train']
    except Exception as e:
        logger.error(f"Error fetching dataset from Hugging Face: {e}")
        return {"total": 0, "imported": 0, "skipped": 0, "duplicates": 0, "invalid": 0}

    total_dataset_size = len(tickets_ds)
    logger.info(f"Dataset successfully loaded. Total records in raw dataset: {total_dataset_size}")

    # 2. Automatically Inspect & Build Lookup Maps
    cat_map = {row['id']: normalize_category(row['name']) for row in cats_ds}
    
    comments_map: Dict[int, List[str]] = {}
    for c in comments_ds:
        tid = c.get('ticket_id')
        body = c.get('body', '') or ''
        body_clean = re.sub(r'\s+', ' ', body).strip()
        if tid and body_clean:
            comments_map.setdefault(tid, []).append(body_clean)

    # 3. Database Initialization & Idempotency Check
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if clear_existing:
        logger.info("Clearing previous Knowledge Base articles for clean fresh seed...")
        db.query(KBArticle).delete()
        db.commit()

    existing_titles: Set[str] = {
        title.lower() for (title,) in db.query(KBArticle.title).all()
    }

    imported_count = 0
    skipped_count = 0
    duplicate_count = 0
    invalid_count = 0
    seen_in_batch: Set[str] = set()

    stop_words = {'the', 'and', 'for', 'not', 'with', 'from', 'this', 'that', 'reported', 'issue', 'users', 'user', 'help', 'desk'}

    # 4. Clean & Process Records
    for i, row in enumerate(tickets_ds):
        if imported_count >= target_count:
            break

        summary = row.get('summary', '') or ''
        description = row.get('description', '') or ''
        affected_service = row.get('affected_service', '') or ''
        department = row.get('requester_department', '') or ''

        # Data Cleaning: Strip whitespace and normalize
        summary_clean = re.sub(r'\s+', ' ', summary).strip()
        desc_clean = re.sub(r'\s+', ' ', description).strip()

        # Validation: Skip invalid/incomplete records missing required fields
        if not summary_clean or not desc_clean or len(summary_clean) < 5 or len(desc_clean) < 5:
            invalid_count += 1
            skipped_count += 1
            continue

        # Formulate distinctive title
        service_label = affected_service.strip().title() if affected_service else ""
        dept_label = department.strip().title() if department else ""
        
        # Build clean title
        title_base = summary_clean.capitalize() if not summary_clean[0].isupper() else summary_clean
        if title_base.endswith('.'):
            title_base = title_base[:-1]

        # Ensure title uniqueness across department/service variations to reach exactly 100 unique SOPs
        if dept_label and service_label:
            title = f"{title_base} ({service_label} - {dept_label})"
        elif dept_label:
            title = f"{title_base} ({dept_label})"
        else:
            title = title_base

        title_lower = title.lower()

        # Idempotency / Duplicate Check
        if title_lower in existing_titles or title_lower in seen_in_batch:
            duplicate_count += 1
            continue

        seen_in_batch.add(title_lower)

        # Normalize Category
        cat_id = row.get('category_id')
        raw_cat_name = cat_map.get(cat_id, affected_service)
        category = normalize_category(raw_cat_name)

        # Map Problem Description
        problem = f"{desc_clean}\n\nContext: Issue reported in {dept_label or 'Corporate'} department affecting {service_label or 'IT Systems'}."

        # Synthesize Solution SOP from Comments
        tid = row.get('ticket_id')
        t_comments = comments_map.get(tid, [])

        unique_comments = []
        for comm in t_comments:
            if comm not in unique_comments:
                unique_comments.append(comm)

        if unique_comments:
            steps = "\n".join([f"{idx+1}. {comm}" for idx, comm in enumerate(unique_comments[:4])])
            solution = (
                f"Standard Operating Fix & Investigation Steps:\n{steps}\n\n"
                f"Verification Protocol:\n"
                f"- Confirm service operational status for '{service_label or 'IT Service'}'.\n"
                f"- Verify user group permissions for '{dept_label or 'Department'}'."
            )
        else:
            solution = (
                f"Standard Operating Resolution for {category}:\n"
                f"1. Verify active network & authentication status for user in {dept_label or 'Department'}.\n"
                f"2. Inspect service logs for {service_label or 'Affected Service'}.\n"
                f"3. Reset local service cache or restart client software.\n"
                f"4. Confirm resolution with requester."
            )

        # Extract Keywords
        words = re.findall(r'\b[a-zA-Z]{3,}\b', f"{title_base} {category} {service_label} {dept_label}".lower())
        filtered_words = [w for w in words if w not in stop_words]
        keywords = ", ".join(list(dict.fromkeys(filtered_words))[:6])

        # Instantiate Model
        kb_article = KBArticle(
            title=title,
            category=category,
            problem=problem,
            solution=solution,
            keywords=keywords
        )

        db.add(kb_article)
        imported_count += 1
        existing_titles.add(title_lower)

        logger.debug(f"[{imported_count}/{target_count}] Imported KB Article: '{title}' [{category}]")

    db.commit()
    db.close()

    stats = {
        "total": total_dataset_size,
        "imported": imported_count,
        "skipped": skipped_count,
        "duplicates": duplicate_count,
        "invalid": invalid_count
    }

    # Print Formatted Statistics Output
    print("\n" + "=" * 52)
    print("📊 HUGGING FACE DATASET IMPORT STATISTICS")
    print("=" * 52)
    print(f"Dataset Size (Total Examined): {stats['total']}")
    print(f"Successfully Imported:         {stats['imported']}")
    print(f"Skipped / Incomplete Rows:     {stats['skipped']}")
    print(f"Duplicate Rows Filtered:       {stats['duplicates']}")
    print(f"Invalid Records Ignored:       {stats['invalid']}")
    print(f"Import Target Achieved:        {stats['imported']}/{target_count}")
    print("=" * 52 + "\n")

    return stats


if __name__ == "__main__":
    import_huggingface_dataset(target_count=100, clear_existing=True)
