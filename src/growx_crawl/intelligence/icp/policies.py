"""
GrowX ICP Evaluation Policies.
Defines scoring thresholds, weights, and confidence penalty rules.
"""

from pydantic import BaseModel


class ICPEvaluationPolicy(BaseModel):
    """Configurable scoring rules and thresholds for ICP matching."""
    policy_version: str = "v1"

    # Fit status thresholds
    min_fit_excellent: float = 0.85
    min_fit_strong: float = 0.70
    min_fit_possible: float = 0.50
    min_fit_weak: float = 0.30

    # Dimension category weights
    firmographic_weight: float = 0.30
    technographic_weight: float = 0.20
    geographic_weight: float = 0.15
    operational_weight: float = 0.15
    signal_weight: float = 0.20

    # Missing data policy: unknown criteria reduce confidence, not fit score
    missing_data_confidence_penalty: float = 0.15
    minimum_data_confidence_gate: float = 0.30


DEFAULT_ICP_POLICY = ICPEvaluationPolicy()
