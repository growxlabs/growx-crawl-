import json
from typing import Any, Dict, Optional
from growx_crawl.intelligence.facts.models import FactEntity, FactPredicateEntity
from growx_crawl.intelligence.observations.models import ObservationEntity


def values_are_equal(v1: Any, v2: Any) -> bool:
    """
    Compares two structured or primitive fact values for logical equivalence.
    """
    if v1 is None and v2 is None:
        return True
    if v1 is None or v2 is None:
        return False

    if isinstance(v1, dict) and isinstance(v2, dict):
        # Compare key metrics if present (e.g. min, max, value)
        if "value" in v1 and "value" in v2:
            return v1["value"] == v2["value"]
        if "min" in v1 and "min" in v2 and "max" in v1 and "max" in v2:
            return v1["min"] == v2["min"] and v1["max"] == v2["max"]
        return json.dumps(v1, sort_keys=True) == json.dumps(v2, sort_keys=True)

    return str(v1).strip().lower() == str(v2).strip().lower()


def evaluate_fact_transition(
    existing_fact: Optional[FactEntity],
    new_obs: ObservationEntity,
    predicate_def: FactPredicateEntity,
    source_authority_class: str = "first_party",
) -> str:
    """
    Evaluates whether a new observation updates, supersedes, conflicts, or coexists
    with existing canonical facts per Sections 48, 49, 52, 53, 54, 55.
    
    Returns: 'create', 'same_value', 'coexist', 'supersede', 'conflict'
    """
    if not existing_fact:
        return "create"

    # Multi-value predicates (technologies, products, services) coexist
    if predicate_def.cardinality == "many":
        if values_are_equal(existing_fact.current_value_json, new_obs.normalized_value_json):
            return "same_value"
        return "coexist"

    # Single-value predicate: compare values
    if values_are_equal(existing_fact.current_value_json, new_obs.normalized_value_json):
        return "same_value"

    # Different value observed for a single-value predicate
    # If predicate policy is conflict_on_disagree, immediately mark conflict
    if predicate_def.merge_policy == "conflict_on_disagree":
        return "conflict"

    # If source is official/registry or higher authority than existing fact, or same source newer observation
    if source_authority_class in ["official", "registry", "first_party"] and new_obs.confidence >= existing_fact.confidence:
        return "supersede"

    return "conflict"
