"""
GrowX Competitor Overlap Scoring & Relationship Classification.
Computes multi-dimensional overlap, strength, confidence, and relationship type.
"""

from typing import Any, Dict, List, Optional, Set
from growx_crawl.intelligence.competitors.models import (
    CompetitiveProfile,
    CompetitorEvidenceEntity,
    EvidenceType,
    RelationshipType,
)
from growx_crawl.intelligence.competitors.policies import (
    CompetitorVerificationPolicy,
    DEFAULT_COMPETITOR_POLICY,
)


def _normalize_tokens(items: List[str]) -> Set[str]:
    """Tokenizes and normalizes strings for set comparisons."""
    tokens = set()
    for item in items:
        if not item:
            continue
        cleaned = item.strip().lower()
        tokens.add(cleaned)
        # Also split phrases into words if multi-word
        words = cleaned.replace("/", " ").replace("-", " ").split()
        if len(words) > 1:
            for w in words:
                if len(w) > 2:
                    tokens.add(w)
    return tokens


def jaccard_similarity(items_a: List[str], items_b: List[str]) -> float:
    """Computes Jaccard similarity between two token sets."""
    set_a = _normalize_tokens(items_a)
    set_b = _normalize_tokens(items_b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return round(len(intersection) / len(union), 3)


def calculate_market_overlap(profile_a: CompetitiveProfile, profile_b: CompetitiveProfile) -> float:
    """Computes market overlap score (0.0–1.0) based on industry and buying problems."""
    ind_sim = jaccard_similarity(profile_a.industries, profile_b.industries)
    prob_sim = jaccard_similarity(profile_a.buying_problems, profile_b.buying_problems)

    if ind_sim > 0 and prob_sim > 0:
        return round((ind_sim * 0.6) + (prob_sim * 0.4), 3)
    if ind_sim > 0:
        return ind_sim
    if prob_sim > 0:
        return round(prob_sim * 0.7, 3)
    return 0.0


def calculate_offering_overlap(profile_a: CompetitiveProfile, profile_b: CompetitiveProfile) -> float:
    """Computes offering overlap score (0.0–1.0) based on products, services, and positioning."""
    prod_sim = jaccard_similarity(profile_a.products, profile_b.products)
    serv_sim = jaccard_similarity(profile_a.services, profile_b.services)
    pos_sim = jaccard_similarity(profile_a.positioning_terms, profile_b.positioning_terms)

    # Weighted composite of offerings
    scores = []
    if prod_sim > 0:
        scores.append(prod_sim * 1.0)
    if serv_sim > 0:
        scores.append(serv_sim * 0.8)
    if pos_sim > 0:
        scores.append(pos_sim * 0.6)

    if not scores:
        return 0.0
    return min(1.0, round(max(scores) * 0.7 + (sum(scores) / len(scores)) * 0.3, 3))


def calculate_customer_overlap(profile_a: CompetitiveProfile, profile_b: CompetitiveProfile) -> float:
    """Computes customer overlap score (0.0–1.0) based on target personas and size bands."""
    cust_sim = jaccard_similarity(profile_a.target_customers, profile_b.target_customers)

    # Compare company size if both known
    size_sim = 0.5  # neutral default
    if profile_a.company_size and profile_b.company_size:
        size_a = profile_a.company_size.strip().lower()
        size_b = profile_b.company_size.strip().lower()
        size_sim = 1.0 if size_a == size_b else 0.2

    if cust_sim > 0:
        return round((cust_sim * 0.75) + (size_sim * 0.25), 3)
    return round(size_sim * 0.4, 3) if profile_a.company_size and profile_b.company_size else 0.0


def calculate_geography_overlap(profile_a: CompetitiveProfile, profile_b: CompetitiveProfile) -> float:
    """Computes geography overlap score (0.0–1.0). Handles global presence."""
    geo_a = {g.strip().lower() for g in profile_a.geographies if g}
    geo_b = {g.strip().lower() for g in profile_b.geographies if g}

    if not geo_a or not geo_b:
        return 0.5  # unknown geography treated with moderate overlap

    # Check for global tags
    global_terms = {"global", "worldwide", "international", "remote"}
    if geo_a.intersection(global_terms) or geo_b.intersection(global_terms):
        return 0.85

    sim = jaccard_similarity(list(geo_a), list(geo_b))
    return sim


def calculate_strength(
    market_overlap: float,
    offering_overlap: float,
    customer_overlap: float,
    geography_overlap: float,
    explicit_evidence_count: int = 0,
    policy: CompetitorVerificationPolicy = DEFAULT_COMPETITOR_POLICY,
) -> float:
    """
    Computes competitor relationship strength (0.0–1.0).
    Represents how fiercely two companies compete in the real market.
    """
    explicit_boost = min(1.0, explicit_evidence_count * 0.5)

    strength = (
        (offering_overlap * policy.offering_weight)
        + (customer_overlap * policy.customer_weight)
        + (market_overlap * policy.market_weight)
        + (geography_overlap * policy.geography_weight)
        + (explicit_boost * policy.explicit_evidence_weight)
    )
    return min(1.0, max(0.0, round(strength, 3)))


def calculate_confidence(
    evidence_list: List[CompetitorEvidenceEntity],
    profile_a_quality: float = 1.0,
    profile_b_quality: float = 1.0,
) -> float:
    """
    Computes GrowX confidence in the relationship evaluation (0.0–1.0).
    Separate from strength: represents how certain we are based on evidence & data quality.
    """
    if not evidence_list:
        base_confidence = 0.35
    else:
        # Evaluate evidence diversity and quantity
        evidence_types = {e.evidence_type for e in evidence_list}
        avg_ev_conf = sum(e.confidence for e in evidence_list) / len(evidence_list)

        # Diverse sources increase confidence
        diversity_multiplier = min(1.2, 0.8 + (len(evidence_types) * 0.15))
        base_confidence = min(0.95, avg_ev_conf * diversity_multiplier)

    # Bound confidence by source data quality (Section 76)
    quality_factor = (profile_a_quality + profile_b_quality) / 2.0
    composite_confidence = base_confidence * quality_factor
    return min(1.0, max(0.1, round(composite_confidence, 3)))


def classify_relationship_type(
    strength: float,
    market_overlap: float,
    offering_overlap: float,
    customer_overlap: float,
    geography_overlap: float,
    policy: CompetitorVerificationPolicy = DEFAULT_COMPETITOR_POLICY,
) -> str:
    """Classifies the relationship type based on multi-dimensional overlap profiles."""
    # Check for regional competition
    if geography_overlap < 0.25 and geography_overlap > 0.0 and offering_overlap >= 0.50:
        return RelationshipType.REGIONAL.value

    # Direct competitors: high offering and market/customer overlap with sufficient strength
    if (
        strength >= policy.min_strength_direct
        and offering_overlap >= 0.30
        and (market_overlap >= 0.25 or customer_overlap >= 0.25)
    ):
        return RelationshipType.DIRECT.value

    # Adjacent competitors: shared customer segment or complementary offerings in same market
    if (
        strength >= policy.min_strength_adjacent
        and (customer_overlap >= 0.40 or (offering_overlap >= 0.15 and market_overlap >= 0.25))
    ):
        return RelationshipType.ADJACENT.value

    # Substitute: solve same buying problem with distinct approach (low offering overlap < 0.15, but shared market/problem)
    if (
        strength >= policy.min_strength_substitute
        and market_overlap >= 0.30
        and offering_overlap < 0.15
    ):
        return RelationshipType.SUBSTITUTE.value

    # Emerging competition
    if strength >= 0.20:
        return RelationshipType.EMERGING.value

    return RelationshipType.UNKNOWN.value

