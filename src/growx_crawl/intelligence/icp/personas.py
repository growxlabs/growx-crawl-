"""
GrowX ICP Buyer Persona Intelligence.
Provides title normalization, role taxonomy mapping, and decision-maker matching.
"""

from typing import Any, Dict, List, Optional, Tuple
from growx_crawl.intelligence.icp.models import ICPPersonaEntity, ReasonCode


ROLE_TAXONOMY = {
    "executive": ["ceo", "founder", "managing director", "president", "co-founder", "partner"],
    "technology": ["cto", "cio", "vp it", "head of it", "director of it", "chief technology officer", "chief information officer", "architect"],
    "operations": ["coo", "head of operations", "vp operations", "operations director", "plant head", "general manager"],
    "engineering": ["vp engineering", "head of engineering", "engineering director", "lead engineer"],
    "finance": ["cfo", "head of finance", "finance director", "controller"],
    "procurement": ["head of procurement", "procurement manager", "supply chain director", "sourcing head"],
    "sales": ["cro", "vp sales", "head of sales", "sales director", "business development"],
    "marketing": ["cmo", "vp marketing", "head of marketing", "growth director"],
}


def normalize_title(title: str) -> str:
    """Normalizes raw job title strings into canonical comparable tokens."""
    if not title:
        return ""
    t = title.strip().lower()
    replacements = {
        "vp ": "vice president ",
        "vp,": "vice president,",
        "dir ": "director ",
        "mgr ": "manager ",
        "sr.": "senior",
        "jr.": "junior",
        "it": "information technology",
    }
    for old, new in replacements.items():
        if old in t:
            t = t.replace(old, new)
    return " ".join(t.split())


class PersonaMatcher:
    """Matches prospect individuals against ICP target buyer personas."""

    def match_person(
        self,
        personas: List[ICPPersonaEntity],
        person_data: Dict[str, Any],
    ) -> Tuple[Optional[ICPPersonaEntity], float, Optional[str], List[str]]:
        """
        Evaluates a person record against target personas.
        Returns:
            matched_persona: the best matching persona entity or None.
            fit_score: 0.0–1.0 score indicating role match and seniority.
            matched_role: normalized role label.
            reasons: list of reason codes.
        """
        raw_title = person_data.get("title") or person_data.get("role") or ""
        norm_title = normalize_title(raw_title)

        if not norm_title:
            return None, 0.0, None, [ReasonCode.INSUFFICIENT_DATA.value]

        best_persona: Optional[ICPPersonaEntity] = None
        best_score = 0.0
        best_matched_pattern: Optional[str] = None
        reasons: List[str] = []

        for persona in personas:
            # Check pattern matches
            score = 0.0
            matched_pattern = None

            for pattern in persona.title_patterns:
                p_norm = normalize_title(pattern)
                if p_norm in norm_title or norm_title in p_norm:
                    score = max(score, 0.85)
                    matched_pattern = pattern
                    break
                # Partial token overlap
                p_tokens = set(p_norm.split())
                t_tokens = set(norm_title.split())
                overlap = p_tokens.intersection(t_tokens)
                if overlap and len(overlap) >= 2:
                    score = max(score, 0.65)
                    matched_pattern = pattern

            # Seniority check
            if persona.seniority and persona.seniority.lower() in norm_title:
                score = min(1.0, score + 0.15)

            # Weight by persona priority (priority 1 gets slight boost)
            if persona.priority == 1:
                score = min(1.0, score * 1.1)

            if score > best_score:
                best_score = score
                best_persona = persona
                best_matched_pattern = matched_pattern or raw_title

        if best_persona and best_score >= 0.50:
            reasons.append(ReasonCode.PERSONA_TITLE_MATCH.value)
            if best_score >= 0.75:
                reasons.append(ReasonCode.PERSONA_SENIORITY_MATCH.value)
            return best_persona, round(best_score, 3), best_matched_pattern, reasons

        return None, 0.0, None, []
