"""
Operator Feedback Service for capturing and aggregating quality review findings.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import sqlite3

from growx_crawl.feedback.models import FeedbackType, OperatorFeedbackEntity
from growx_crawl.storage.db import get_db
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

logger = logging.getLogger("growx_crawl.feedback.service")


class OperatorFeedbackService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        with get_db(self.db_path) as conn:
            init_sqlite_canonical_tables(conn)

    def submit_feedback(
        self,
        actor_id: str,
        subject_type: str,
        subject_id: str,
        feedback_type: FeedbackType,
        notes: Optional[str] = None,
    ) -> OperatorFeedbackEntity:
        feedback = OperatorFeedbackEntity(
            actor_id=actor_id,
            subject_type=subject_type,
            subject_id=subject_id,
            feedback_type=feedback_type,
            notes=notes,
        )
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO operator_feedback (id, actor_id, subject_type, subject_id, feedback_type, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.id,
                    feedback.actor_id,
                    feedback.subject_type,
                    feedback.subject_id,
                    feedback.feedback_type.value,
                    feedback.notes,
                    feedback.created_at,
                ),
            )
        logger.info(f"[FEEDBACK] Recorded {feedback_type.value} feedback for {subject_type}:{subject_id} by {actor_id}")
        return feedback

    def list_feedback(
        self,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 100,
    ) -> List[OperatorFeedbackEntity]:
        with get_db(self.db_path) as conn:
            clauses = []
            params = []
            if subject_type:
                clauses.append("subject_type = ?")
                params.append(subject_type)
            if subject_id:
                clauses.append("subject_id = ?")
                params.append(subject_id)
            if feedback_type:
                clauses.append("feedback_type = ?")
                params.append(feedback_type.value if isinstance(feedback_type, FeedbackType) else str(feedback_type))

            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM operator_feedback {where} ORDER BY created_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
            return [
                OperatorFeedbackEntity(
                    id=r["id"],
                    actor_id=r["actor_id"],
                    subject_type=r["subject_type"],
                    subject_id=r["subject_id"],
                    feedback_type=FeedbackType(r["feedback_type"]),
                    notes=r["notes"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def get_summary(self) -> Dict[str, Any]:
        with get_db(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM operator_feedback;").fetchone()[0]
            by_type = conn.execute("SELECT feedback_type, COUNT(*) as cnt FROM operator_feedback GROUP BY feedback_type;").fetchall()
            counts = {r["feedback_type"]: r["cnt"] for r in by_type}
            return {
                "total_feedback_count": total,
                "breakdown_by_type": counts,
                "accuracy_sentiment": round(counts.get("correct", 0) / max(1, total), 3),
            }


operator_feedback_service = OperatorFeedbackService()

__all__ = [
    "OperatorFeedbackService",
    "operator_feedback_service",
]
