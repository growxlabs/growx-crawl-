from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TargetStatus(str, Enum):
    QUEUED = "queued"
    FETCHING = "fetching"
    PARSED = "parsed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPLETED = "completed"


class PriorityLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class MatchDecision(str, Enum):
    AUTO_MERGED = "auto_merged"
    REVIEW_REQUIRED = "review_required"
    DISTINCT = "distinct"
