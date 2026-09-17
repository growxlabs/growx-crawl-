"""
Operator Feedback Domain Models for Ground-Truth Review.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from growx_crawl.shared.ids import generate_id


class FeedbackType(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"
    WRONG_FIT = "wrong_fit"
    WRONG_PERSON = "wrong_person"
    BAD_DATA = "bad_data"


class OperatorFeedbackEntity(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("fbk"))
    actor_id: str
    subject_type: str  # "prospect", "company", "person", "fact", "signal"
    subject_id: str
    feedback_type: FeedbackType
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
