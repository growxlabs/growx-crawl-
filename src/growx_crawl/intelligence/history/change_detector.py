"""
GrowX Fact History Change Detector.
Identifies significant semantic changes between past and new fact values.
"""

from typing import Any, Dict, Optional


def detect_value_change(
    old_value: Any,
    new_value: Any,
    predicate: str,
) -> Optional[Dict[str, Any]]:
    """
    Compares previous canonical value with new value.
    Returns change descriptor dictionary if significant change occurred, else None.
    """
    if old_value == new_value:
        return None

    change_type = "updated"
    if predicate == "company.employee_count":
        try:
            old_num = int(old_value) if isinstance(old_value, (int, str)) and str(old_value).isdigit() else None
            new_num = int(new_value) if isinstance(new_value, (int, str)) and str(new_value).isdigit() else None
            if old_num and new_num:
                if new_num > old_num:
                    change_type = "headcount_growth"
                elif new_num < old_num:
                    change_type = "headcount_contraction"
        except Exception:
            pass

    return {
        "predicate": predicate,
        "old_value": old_value,
        "new_value": new_value,
        "change_type": change_type,
    }
