import sys
import os
import re
import logging
from typing import Set

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import KBArticle

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("dataset_import")


def import_huggingface_dataset(max_records: int = 200, clear_existing: bool = False):
    """
    Downloads and imports support ticket data from Hugging Face (mindweave/help-desk-tickets).
    Cleans data, normalizes whitespace, maps fields to KBArticle schema, deduplicates,
    and persists records to the SQLite database.
    """
    logger.info("Starting Hugging Face dataset import (mindweave/help-desk-tickets)...")

    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please run 'pip install datasets'.")
        sys.exit(1)

    # 1. Download Dataset Splits
    logger.info("Fetching dataset splits from Hugging Face...")
    try:
        cats_ds = load_dataset('mindweave/help-desk-tickets', 'categories')['train']
        tickets_ds = load_dataset('mindweave/help-desk-tickets', 'tickets')['train']
        comments_ds = load_dataset('mindweave/help-desk-tickets', 'comments')['train']
    except Exception as e:
        logger.error(f"Failed to load dataset from Hugging Face: {e}")
        return

    total_rows = len(tickets_ds)
    logger.info(f"Successfully retrieved {total_rows} ticket records from Hugging Face dataset.")

    # 2. Build Lookup Maps
    cat_map = {row['id']: row['name'] for row in cats_ds}
    
    comments_map = {}
    for c in comments_ds:
        tid = c.get('ticket_id')
        body = c.get('body', '') or ''
        body_clean = re.sub(r'\s+', ' ', body).strip()
        if tid and body_clean:
            comments_map.setdefault(tid, []).append(body_clean)

    # 3. Connect to DB & Fetch Existing Titles to Avoid Duplicates
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if clear_existing:
        logger.info("Clearing existing Knowledge Base records before import...")
        db.query(KBArticle).delete()
        db.commit()

    existing_titles: Set[str] = {
        title.lower() for (title,) in db.query(KBArticle.title).all()
    }

    imported_count = 0
    skipped_count = 0
    duplicate_count = 0
    seen_in_batch: Set[str] = set()

    stop_words = {'the', 'and', 'for', 'not', 'with', 'from', 'this', 'that', 'reported', 'issue', 'users', 'user', 'help', 'desk'}

    # 4. Process and Clean Dataset Rows
    for row in tickets_ds:
        if imported_count >= max_records:
            break

        summary = row.get('summary', '') or ''
        description = row.get('description', '') or ''

        # Data Cleaning: Normalize whitespace
        summary_clean = re.sub(r'\s+', ' ', summary).strip()
        description_clean = re.sub(r'\s+', ' ', description).strip()

        # Data Cleaning: Remove empty/incomplete records
        if not summary_clean or len(summary_clean) < 5:
            skipped_count += 1
            continue

        title = summary_clean.capitalize() if not summary_clean[0].isupper() else summary_clean
        title_lower = title.lower()

        # Deduplication check
        if title_lower in existing_titles or title_lower in seen_in_batch:
            duplicate_count += 1
            continue

        seen_in_batch.add(title_lower)

        # Mapping fields
        cat_id = row.get('category_id')
        category = cat_map.get(cat_id, 'General IT')

        problem = description_clean if len(description_clean) >= 10 else f"Reported issue: {title}"

        # Synthesize Resolution from Comments & Metadata
        tid = row.get('ticket_id')
        t_comments = comments_map.get(tid, [])

        unique_comments = []
        for comm in t_comments:
            if comm not in unique_comments:
                unique_comments.append(comm)

        service = row.get('affected_service', '') or 'IT Service'
        dept = row.get('requester_department', '') or 'Corporate Department'

        if unique_comments:
            steps = "\n".join([f"{i+1}. {comm}" for i, comm in enumerate(unique_comments[:4])])
            solution = (
                f"Standard Operating Procedure & Resolution Steps:\n{steps}\n\n"
                f"Service Context:\n- Affected Service: {service}\n- User Department: {dept}"
            )
        else:
            solution = (
                f"Standard Resolution Steps for {category}:\n"
                f"1. Verify service status for '{service}'.\n"
                f"2. Confirm user authorization for '{dept}' group.\n"
                f"3. Clear local application cache or restart client service.\n"
                f"4. Contact Tier-2 support if error persists."
            )

        # Extract Keywords
        words = re.findall(r'\b[a-zA-Z]{3,}\b', f"{title} {category} {service} {dept}".lower())
        filtered_words = [w for w in words if w not in stop_words]
        keywords = ", ".join(list(dict.fromkeys(filtered_words))[:6])

        # Create KBArticle Model Instance
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

    db.commit()
    db.close()

    # 5. Log Summary
    print("\n" + "=" * 52)
    print("📊 HUGGING FACE DATASET IMPORT SUMMARY")
    print("=" * 52)
    print(f"Dataset Name:                 mindweave/help-desk-tickets")
    print(f"Total Dataset Rows Examined:  {total_rows}")
    print(f"Successfully Imported Rows:   {imported_count}")
    print(f"Duplicate Rows Filtered:     {duplicate_count}")
    print(f"Skipped / Incomplete Rows:   {skipped_count}")
    print(f"Import Cap Target:            {max_records}")
    print("=" * 52 + "\n")


if __name__ == "__main__":
    import_huggingface_dataset()
