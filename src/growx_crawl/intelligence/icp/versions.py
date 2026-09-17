"""
GrowX ICP Version Manager.
Governs version immutability, activation state transitions, and version comparisons.
"""

from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.intelligence.icp.models import (
    ICPCriterionEntity,
    ICPExclusionEntity,
    ICPPersonaEntity,
    ICPStatus,
    ICPVersionEntity,
)


class ICPVersionManager:
    """Manages immutable version lifecycles and comparison diffs."""

    @staticmethod
    def can_mutate_version(version: ICPVersionEntity) -> bool:
        """Active and archived versions are strictly immutable (Section 10)."""
        return version.status == ICPStatus.DRAFT.value

    @staticmethod
    def activate_version(
        target_version: ICPVersionEntity,
        all_versions: List[ICPVersionEntity],
    ) -> Tuple[ICPVersionEntity, List[ICPVersionEntity]]:
        """
        Activates target version and transitions any currently active versions to superseded.
        Returns (activated_target, list_of_superseded_versions).
        """
        superseded: List[ICPVersionEntity] = []
        for v in all_versions:
            if v.id != target_version.id and v.status == ICPStatus.ACTIVE.value:
                v.status = ICPStatus.SUPERSEDED.value
                superseded.append(v)

        target_version.status = ICPStatus.ACTIVE.value
        return target_version, superseded

    @staticmethod
    def compare_versions(
        criteria_a: List[ICPCriterionEntity],
        criteria_b: List[ICPCriterionEntity],
        exclusions_a: Optional[List[ICPExclusionEntity]] = None,
        exclusions_b: Optional[List[ICPExclusionEntity]] = None,
        personas_a: Optional[List[ICPPersonaEntity]] = None,
        personas_b: Optional[List[ICPPersonaEntity]] = None,
        version_a: Optional[ICPVersionEntity] = None,
        version_b: Optional[ICPVersionEntity] = None,
    ) -> Dict[str, Any]:
        """Produces a structured diff between two ICP versions (Section 95)."""
        excl_a = exclusions_a or []
        excl_b = exclusions_b or []
        pers_a = personas_a or []
        pers_b = personas_b or []

        fields_a = {f"{c.category}:{c.field}:{c.operator}": c for c in criteria_a}
        fields_b = {f"{c.category}:{c.field}:{c.operator}": c for c in criteria_b}

        added_criteria = []
        removed_criteria = []
        weight_changes = []

        for key, crit in fields_b.items():
            if key not in fields_a:
                added_criteria.append({
                    "field": crit.field,
                    "value": crit.value_json,
                    "category": crit.category,
                    "operator": crit.operator,
                })
            elif fields_a[key].weight != crit.weight:
                weight_changes.append({
                    "field": crit.field,
                    "old_weight": fields_a[key].weight,
                    "new_weight": crit.weight,
                })

        for key, crit in fields_a.items():
            if key not in fields_b:
                removed_criteria.append({
                    "field": crit.field,
                    "value": crit.value_json,
                    "category": crit.category,
                    "operator": crit.operator,
                })

        # Exclusions diff
        ex_reasons_a = {e.reason for e in excl_a}
        ex_reasons_b = {e.reason for e in excl_b}

        # Personas diff
        pers_names_a = {p.name for p in pers_a}
        pers_names_b = {p.name for p in pers_b}

        return {
            "version_a_id": version_a.id if version_a else None,
            "version_b_id": version_b.id if version_b else None,
            "criteria": {
                "added": added_criteria,
                "removed": removed_criteria,
                "modified": weight_changes,
            },
            "added_criteria": added_criteria,
            "removed_criteria": removed_criteria,
            "weight_changes": weight_changes,
            "exclusions": {
                "added": list(ex_reasons_b - ex_reasons_a),
                "removed": list(ex_reasons_a - ex_reasons_b),
            },
            "added_exclusions": list(ex_reasons_b - ex_reasons_a),
            "removed_exclusions": list(ex_reasons_a - ex_reasons_b),
            "personas": {
                "added": list(pers_names_b - pers_names_a),
                "removed": list(pers_names_a - pers_names_b),
            },
        }
