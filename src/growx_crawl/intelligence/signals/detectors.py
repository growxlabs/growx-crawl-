"""
GrowX Buying Signal Detectors.
Heuristically extracts high-intent buying signals from observed company data.
"""

from typing import Any, Dict, List
from growx_crawl.intelligence.signals.models import SignalEntity
from growx_crawl.shared.ids import generate_id


def detect_signals_from_company(company_id: str, company_data: Dict[str, Any]) -> List[SignalEntity]:
    """Scans company attributes and returns high-confidence buying and growth signals."""
    signals: List[SignalEntity] = []

    # 1. Check for funding indicator
    funding = company_data.get("funding_stage") or company_data.get("total_funding")
    if funding:
        signals.append(SignalEntity(
            id=generate_id("sig_"),
            entity_id=company_id,
            signal_type="funding_raised",
            title="Capital Infusion / Funding",
            description=f"Company reported active funding stage or capital: {funding}",
            confidence=0.90,
        ))

    # 2. Check for technology modernization
    techs = company_data.get("technologies_used") or []
    if isinstance(techs, list) and len(techs) >= 3:
        signals.append(SignalEntity(
            id=generate_id("sig_"),
            entity_id=company_id,
            signal_type="tech_stack_active",
            title="Modern Tech Stack Observed",
            description=f"Active technologies identified: {', '.join(str(t) for t in techs[:5])}",
            confidence=0.85,
        ))

    return signals
