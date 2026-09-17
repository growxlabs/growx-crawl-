from datetime import datetime, timezone
import re
from typing import Optional


import os


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename ensuring no path traversals or unsafe characters."""
    base = os.path.basename(filename.replace("\\", "/"))
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    clean = re.sub(r"\.{2,}", "_", clean).strip("_.")
    return clean or "artifact.bin"


def build_object_key(
    category: str,
    entity_id: str,
    filename: str,
    object_id: Optional[str] = None,
    date: Optional[datetime] = None,
) -> str:
    """
    Builds a deterministic, PII-free object key following the Section 10 specification:
    Format: <category>/<YYYY/MM/DD>/<entity-or-job>/<object-id>/<filename>
    
    Examples:
        crawl/2026/09/17/cmp_01K.../run_01K.../homepage.html
        screenshots/2026/09/17/cmp_01K.../run_01K.../homepage.webp
        exports/2026/09/17/prj_01K.../exp_01K.../qualified-leads.xlsx
    """
    now = date or datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")

    clean_category = re.sub(r"[^a-zA-Z0-9_-]", "", category.strip().lower()) or "misc"
    clean_entity = re.sub(r"[^a-zA-Z0-9_-]", "", entity_id.strip()) or "global"
    clean_filename = sanitize_filename(filename)

    if object_id:
        clean_obj_id = re.sub(r"[^a-zA-Z0-9_-]", "", object_id.strip())
        return f"{clean_category}/{date_path}/{clean_entity}/{clean_obj_id}/{clean_filename}"
    return f"{clean_category}/{date_path}/{clean_entity}/{clean_filename}"
