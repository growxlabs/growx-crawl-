"""
Phase 10 — Historical Intelligence Tests.
Covers change detection, timelines, trends, signals, idempotency, backfill,
extractor guards, and the full acceptance criteria.
"""

import pytest
from unittest.mock import MagicMock

from growx_crawl.intelligence.history.change_detector import (
    ChangeDetector,
    detect_value_change,
)
from growx_crawl.intelligence.history.models import (
    ChangeEventType,
    Significance,
    TimelineEventEntity,
    TrendEntity,
    CompanyTemporalSummary,
    BackfillRunEntity,
)
from growx_crawl.intelligence.history.significance import SignificanceEngine
from growx_crawl.intelligence.history.policies import ChangePolicy, PolicyRegistry
from growx_crawl.intelligence.history.timelines import TimelineBuilder
from growx_crawl.intelligence.history.trends import EmployeeGrowthCalculator
from growx_crawl.intelligence.history.repository import SqliteHistoricalRepository
from growx_crawl.intelligence.history.service import HistoricalIntelligenceService
from growx_crawl.intelligence.signals.models import (
    SignalCandidateEntity,
    SignalType,
    SignalCandidateStatus,
)
from growx_crawl.intelligence.signals.detectors import (
    SignalCandidateDetector,
    detect_signals_from_company,
)
from growx_crawl.intelligence.signals.scoring import (
    compute_signal_freshness,
    compute_signal_score,
)
from growx_crawl.intelligence.signals.policies import get_signal_expiry_date
from growx_crawl.intelligence.signals.repository import SqliteSignalRepository
from growx_crawl.intelligence.signals.service import SignalService
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


# ── Fixtures ──

@pytest.fixture
def detector():
    return ChangeDetector()


@pytest.fixture
def significance_engine():
    return SignificanceEngine()


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_phase10.db")


@pytest.fixture
def history_repo(tmp_db):
    return SqliteHistoricalRepository(db_path=tmp_db)


@pytest.fixture
def signal_repo(tmp_db):
    return SqliteSignalRepository(db_path=tmp_db)


@pytest.fixture
def history_service(history_repo):
    return HistoricalIntelligenceService(repository=history_repo)


@pytest.fixture
def signal_service(signal_repo):
    return SignalService(repository=signal_repo)


# ── Test 1: Numeric change creates event ──

def test_numeric_change_creates_event(detector):
    """120 -> 180 should create a fact_changed event with correct deltas."""
    event = detector.detect_fact_change(
        entity_type="company",
        entity_id="cmp_test001",
        fact_id="fct_emp001",
        predicate="company.employee_count",
        old_value_json={"value": 120},
        new_value_json={"value": 180},
        occurred_at="2026-04-01T00:00:00Z",
    )

    assert event is not None
    assert event.event_type == ChangeEventType.FACT_CHANGED.value
    assert event.previous_value_json == {"value": 120}
    assert event.new_value_json == {"value": 180}
    assert event.metadata_json["absolute_delta"] == 60.0
    assert event.metadata_json["percentage_delta"] == 50.0
    assert event.fingerprint


# ── Test 2: Formatting-only change does NOT create event ──

def test_formatting_only_change_ignored(detector):
    """'250 employees' vs '~250 employees' should NOT create a change event."""
    event = detector.detect_fact_change(
        entity_type="company",
        entity_id="cmp_test002",
        fact_id="fct_emp002",
        predicate="company.employee_count",
        old_value_json={"value": "250 employees"},
        new_value_json={"value": "~250 employees"},
        occurred_at="2026-05-01T00:00:00Z",
    )

    assert event is None


# ── Test 3: Multi-value add/remove ──

def test_multivalue_add_remove(detector):
    """Technology add/remove should create separate events."""
    events = detector.detect_multivalue_changes(
        entity_type="company",
        entity_id="cmp_test003",
        fact_id="fct_tech003",
        predicate="company.technology",
        old_values=["React", "Node.js", "PostgreSQL"],
        new_values=["React", "PostgreSQL", "Go"],
        occurred_at="2026-06-01T00:00:00Z",
    )

    assert len(events) == 2

    event_types = {e.event_type for e in events}
    assert "technology_added" in event_types
    assert "technology_removed" in event_types

    added = [e for e in events if e.event_type == "technology_added"]
    removed = [e for e in events if e.event_type == "technology_removed"]
    assert added[0].new_value_json["value"] == "Go"
    assert removed[0].previous_value_json["value"] == "Node.js"


# ── Test 4: Employment history ──

def test_employment_change(history_service):
    """Join/leave events should be created correctly."""
    join_event = history_service.process_employment_change(
        person_id="per_test004",
        company_id="cmp_test004",
        event_type=ChangeEventType.EMPLOYMENT_STARTED.value,
        title="VP Engineering",
        occurred_at="2026-03-15T00:00:00Z",
    )

    assert join_event is not None
    assert join_event.event_type == ChangeEventType.EMPLOYMENT_STARTED.value
    assert join_event.new_value_json["company_id"] == "cmp_test004"
    assert join_event.new_value_json["title"] == "VP Engineering"


# ── Test 5: Reappearance ──

def test_reappearance_detection(detector):
    """Removed value reappearing should be detectable."""
    # First, tech was removed
    events = detector.detect_multivalue_changes(
        entity_type="company",
        entity_id="cmp_test005",
        fact_id="fct_tech005",
        predicate="company.technology",
        old_values=["SAP", "Oracle"],
        new_values=["Oracle"],
        occurred_at="2026-01-01T00:00:00Z",
    )
    assert len(events) == 1
    assert events[0].event_type == "technology_removed"

    # Then reappears
    events2 = detector.detect_multivalue_changes(
        entity_type="company",
        entity_id="cmp_test005",
        fact_id="fct_tech005",
        predicate="company.technology",
        old_values=["Oracle"],
        new_values=["Oracle", "SAP"],
        occurred_at="2026-06-01T00:00:00Z",
    )
    assert len(events2) == 1
    assert events2[0].event_type == "technology_added"


# ── Test 6: Trend calculation ──

def test_employee_growth_trend():
    """Employee growth should be computed correctly over a time window."""
    calc = EmployeeGrowthCalculator()
    now_iso = utc_iso_now()

    fact_values = [
        {"value_json": {"value": 120}, "valid_from": "2026-01-01T00:00:00Z", "fact_id": "fct_001"},
        {"value_json": {"value": 180}, "valid_from": "2026-04-01T00:00:00Z", "fact_id": "fct_001"},
        {"value_json": {"value": 260}, "valid_from": "2026-09-01T00:00:00Z", "fact_id": "fct_001"},
    ]

    trend = calc.calculate("company", "cmp_test006", fact_values, window_days=365)

    assert trend is not None
    assert trend.trend_type == "employee_growth"
    assert trend.value_json["earliest_value"] == 120
    assert trend.value_json["latest_value"] == 260
    assert trend.value_json["growth_percentage"] == pytest.approx(116.67, abs=0.01)


# ── Test 7: Idempotency ──

def test_idempotent_event_creation(history_service):
    """Same change processed twice should create only one event."""
    changes = [{
        "fact_id": "fct_test007",
        "predicate": "company.employee_count",
        "old_value_json": {"value": 100},
        "new_value_json": {"value": 200},
        "occurred_at": "2026-07-01T00:00:00Z",
        "confidence": 0.9,
    }]

    # First call creates event
    events1 = history_service.detect_changes("company", "cmp_test007", changes)
    assert len(events1) == 1

    # Second call with identical data should be idempotent (0 new events)
    events2 = history_service.detect_changes("company", "cmp_test007", changes)
    assert len(events2) == 0


# ── Test 8: Backfill ──

def test_historical_backfill(history_service):
    """Old fact history should generate ordered timeline events."""
    history = [
        {
            "entity_id": "cmp_test008",
            "fact_id": "fct_hist001",
            "predicate": "company.employee_count",
            "old_value_json": {},
            "new_value_json": {"value": 50},
            "occurred_at": "2025-01-01T00:00:00Z",
            "confidence": 0.8,
        },
        {
            "entity_id": "cmp_test008",
            "fact_id": "fct_hist002",
            "predicate": "company.employee_count",
            "old_value_json": {"value": 50},
            "new_value_json": {"value": 100},
            "occurred_at": "2025-06-01T00:00:00Z",
            "confidence": 0.85,
        },
    ]

    run = history_service.backfill("company", history)
    assert run.status == "completed"
    assert run.processed_count == 2
    assert run.error_count == 0

    # Verify timeline has events in order
    timeline = history_service.get_timeline("company", "cmp_test008")
    assert len(timeline) >= 2
    # Chronological order
    assert timeline[0]["occurred_at"] <= timeline[1]["occurred_at"]


# ── Test 9: Extractor version guard ──

def test_extractor_version_guard(detector):
    """Interpretation change should NOT create a real-world change event."""
    event = detector.detect_fact_change(
        entity_type="company",
        entity_id="cmp_test009",
        fact_id="fct_ext009",
        predicate="company.employee_count",
        old_value_json={"value": 200},
        new_value_json={"value": 205},
        occurred_at="2026-08-01T00:00:00Z",
        old_extractor_version="v1.0",
        new_extractor_version="v2.0",
    )

    assert event is not None
    assert event.event_type == ChangeEventType.INTERPRETATION_REVISED.value
    assert event.metadata_json.get("reason") == "extractor_version_change"
    assert event.confidence < 1.0  # Lower confidence for interpretation changes


# ── Test 10: Significance scoring ──

def test_significance_scoring(significance_engine):
    """Headquarters change should be high, blog change should be low."""
    hq_sig = significance_engine.evaluate(
        event_type="fact_changed",
        predicate="company.headquarters",
    )
    assert hq_sig == Significance.HIGH.value

    desc_sig = significance_engine.evaluate(
        event_type="fact_changed",
        predicate="company.description",
    )
    assert desc_sig == Significance.LOW.value


# ── Test 11: Signal candidate creation ──

def test_signal_candidate_from_timeline():
    """Timeline events should produce signal candidates."""
    detector = SignalCandidateDetector()

    events = [
        TimelineEventEntity(
            id=generate_id("evt_"),
            entity_type="company",
            entity_id="cmp_test011",
            event_type="technology_added",
            occurred_at="2026-09-01T00:00:00Z",
            predicate="company.technology",
            new_value_json={"value": "SAP"},
            significance="medium",
            fingerprint="fp_test011a",
        ),
        TimelineEventEntity(
            id=generate_id("evt_"),
            entity_type="company",
            entity_id="cmp_test011",
            event_type="fact_changed",
            occurred_at="2026-09-02T00:00:00Z",
            predicate="company.employee_count",
            previous_value_json={"value": 100},
            new_value_json={"value": 200},
            significance="high",
            fingerprint="fp_test011b",
        ),
    ]

    candidates = detector.detect_from_timeline_events("cmp_test011", events)
    assert len(candidates) == 2

    types = {c.signal_type for c in candidates}
    assert SignalType.TECHNOLOGY_ADOPTION.value in types
    assert SignalType.HIRING_GROWTH.value in types


# ── Test 12: Signal freshness and expiry ──

def test_signal_freshness_and_expiry():
    """Old signals should have low freshness; expiry dates should be computed."""
    from datetime import timedelta
    from growx_crawl.shared.time import format_iso, utc_now

    # Fresh signal (just detected)
    fresh = SignalCandidateEntity(
        id="sigc_fresh",
        entity_id="cmp_test012",
        signal_type="hiring_growth",
        detected_at=utc_iso_now(),
    )
    freshness = compute_signal_freshness(fresh)
    assert freshness > 0.9  # Very fresh

    # Old signal (detected 90 days ago — past midpoint of 60-day window)
    old_date = format_iso(utc_now() - timedelta(days=90))
    old = SignalCandidateEntity(
        id="sigc_old",
        entity_id="cmp_test012",
        signal_type="hiring_growth",
        detected_at=old_date or "",
    )
    old_freshness = compute_signal_freshness(old)
    assert old_freshness == 0.0  # Past expiry window (60 days for hiring)

    # Expiry date computation
    expiry = get_signal_expiry_date("leadership_change")
    assert expiry  # Should return a valid ISO date


# ── Test 13: State reconstruction ──

def test_state_reconstruction():
    """get_state_at should return correct historical state."""
    builder = TimelineBuilder()

    facts = [
        {"id": "fct_sr001", "predicate": "company.employee_count"},
        {"id": "fct_sr002", "predicate": "company.headquarters"},
    ]

    values = [
        {
            "fact_id": "fct_sr001",
            "value_json": {"value": 120},
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_to": "2026-06-01T00:00:00Z",
            "confidence": 0.85,
            "status": "superseded",
        },
        {
            "fact_id": "fct_sr001",
            "value_json": {"value": 180},
            "valid_from": "2026-06-01T00:00:00Z",
            "valid_to": None,
            "confidence": 0.9,
            "status": "accepted",
        },
        {
            "fact_id": "fct_sr002",
            "value_json": {"value": "Hyderabad"},
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_to": None,
            "confidence": 0.95,
            "status": "accepted",
        },
    ]

    # State in March 2026 — should show employee_count=120
    state_march = builder.reconstruct_state_at(facts, values, "2026-03-15T00:00:00Z")
    assert "company.employee_count" in state_march
    assert state_march["company.employee_count"]["value"] == {"value": 120}

    # State in September 2026 — should show employee_count=180
    state_sept = builder.reconstruct_state_at(facts, values, "2026-09-01T00:00:00Z")
    assert state_sept["company.employee_count"]["value"] == {"value": 180}
    assert state_sept["company.headquarters"]["value"] == {"value": "Hyderabad"}


# ── Test 14: Range transition ──

def test_range_transition_detection(detector):
    """51-200 -> 201-500 should be detected as a range change."""
    event = detector.detect_fact_change(
        entity_type="company",
        entity_id="cmp_test014",
        fact_id="fct_range014",
        predicate="company.employee_range",
        old_value_json={"value": "51-200"},
        new_value_json={"value": "201-500"},
        occurred_at="2026-07-01T00:00:00Z",
    )

    assert event is not None
    assert event.event_type == ChangeEventType.FACT_CHANGED.value
    assert event.metadata_json.get("range_transition") is not None
    range_info = event.metadata_json["range_transition"]
    assert range_info["old_range"] == (51, 200)
    assert range_info["new_range"] == (201, 500)


# ── Test 15: Timeline retrieval ──

def test_timeline_retrieval(history_service):
    """Timeline should return events in chronological order with evidence refs."""
    # Create events via change detection
    changes = [
        {
            "fact_id": "fct_tl001",
            "predicate": "company.employee_count",
            "old_value_json": {"value": 50},
            "new_value_json": {"value": 100},
            "occurred_at": "2026-01-15T00:00:00Z",
            "confidence": 0.8,
        },
        {
            "fact_id": "fct_tl002",
            "predicate": "company.headquarters",
            "old_value_json": {"value": "Mumbai"},
            "new_value_json": {"value": "Hyderabad"},
            "occurred_at": "2026-03-20T00:00:00Z",
            "confidence": 0.9,
        },
    ]

    events = history_service.detect_changes("company", "cmp_test015", changes)
    assert len(events) == 2

    # Retrieve timeline
    timeline = history_service.get_timeline("company", "cmp_test015")
    assert len(timeline) == 2
    assert timeline[0]["occurred_at"] <= timeline[1]["occurred_at"]

    # Verify structure
    assert "event_type" in timeline[0]
    assert "significance" in timeline[0]
    assert "confidence" in timeline[0]
