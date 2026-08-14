from sqlalchemy.orm import Session
from sqlalchemy import or_, select, func
from typing import List, Optional
from app.models import KBArticle
from app.schemas import KBArticleCreate


class KBService:
    """Service layer for managing Knowledge Base articles and AI lookup compatibility."""

    @staticmethod
    def get_all_articles(db: Session, skip: int = 0, limit: int = 100) -> List[KBArticle]:
        """Fetch all knowledge base articles with optional pagination."""
        return db.query(KBArticle).order_by(KBArticle.title.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_article_by_id(db: Session, article_id: int) -> Optional[KBArticle]:
        """Fetch a single knowledge base article by ID."""
        return db.query(KBArticle).filter(KBArticle.id == article_id).first()

    @staticmethod
    def get_articles_by_category(db: Session, category: str) -> List[KBArticle]:
        """Fetch articles belonging to a specific category."""
        return db.query(KBArticle).filter(
            func.lower(KBArticle.category) == func.lower(category)
        ).order_by(KBArticle.title.asc()).all()

    @staticmethod
    def search_articles(db: Session, query: Optional[str] = None, category: Optional[str] = None) -> List[KBArticle]:
        """
        Search articles by keyword/text query and/or filter by category.
        Designed for search bar filtering and AI KB retrieval.
        """
        stmt = db.query(KBArticle)

        if category and category.strip() and category != "All":
            stmt = stmt.filter(func.lower(KBArticle.category) == func.lower(category.strip()))

        if query and query.strip():
            q_term = f"%{query.strip()}%"
            stmt = stmt.filter(
                or_(
                    KBArticle.title.ilike(q_term),
                    KBArticle.problem.ilike(q_term),
                    KBArticle.solution.ilike(q_term),
                    KBArticle.keywords.ilike(q_term),
                    KBArticle.category.ilike(q_term)
                )
            )

        return stmt.order_by(KBArticle.created_at.desc()).all()

    @staticmethod
    def get_categories(db: Session) -> List[str]:
        """Return distinct category names for filter dropdowns."""
        result = db.query(KBArticle.category).distinct().all()
        categories = sorted([r[0] for r in result if r[0]])
        return categories

    @staticmethod
    def create_article(db: Session, article_in: KBArticleCreate) -> KBArticle:
        """Create and persist a new knowledge base article."""
        article = KBArticle(
            title=article_in.title.strip(),
            category=article_in.category.strip(),
            problem=article_in.problem.strip(),
            solution=article_in.solution.strip(),
            keywords=article_in.keywords.strip() if article_in.keywords else None
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        return article
