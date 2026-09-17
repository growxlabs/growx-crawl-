"""
GrowX Data Factory Scheduler & Concurrency Lock.
Prevents concurrent execution of overlapping factory runs, enforces operating windows,
and manages run lifecycle locks.
"""

import threading
from typing import Optional


class DataFactoryScheduler:
    """Manages active run locks and scheduling windows."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_run_id: Optional[str] = None

    def acquire_run_lock(self, run_id: str) -> bool:
        """Attempts to claim exclusive execution lock for a run."""
        with self._lock:
            if self._active_run_id is not None and self._active_run_id != run_id:
                return False
            self._active_run_id = run_id
            return True

    def release_run_lock(self, run_id: str) -> None:
        """Releases the execution lock if held by the run."""
        with self._lock:
            if self._active_run_id == run_id:
                self._active_run_id = None

    def is_locked(self) -> bool:
        with self._lock:
            return self._active_run_id is not None

    def get_active_run_id(self) -> Optional[str]:
        with self._lock:
            return self._active_run_id


factory_scheduler = DataFactoryScheduler()
