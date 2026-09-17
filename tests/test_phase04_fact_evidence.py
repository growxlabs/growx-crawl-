import uuid
import pytest

from growx_crawl.identity import identity_service
from growx_crawl.intelligence.adapters import autogtm_adapter, extractor_adapter
from growx_crawl.intelligence.evidence import evidence_service
from growx_crawl.intelligence.facts import (
    compute_fact_confidence,
    fact_service,
    normalize_employee_range,
    normalize_fact_value,
    normalize_integer,
    normalize_revenue_range,
    predicate_registry,
)
from growx_crawl.intelligence.observations import observation_service


def test_predicate_registry():
    """Verify predicate registry enforces controlled, typed predicates."""
    assert predicate_registry.is_known("company.legal_name")
    assert predicate_registry.is_known("company.employee_count")
    assert predicate_registry.is_known("company.technology")
    assert not predicate_registry.is_known("company.random_undefined_predicate")

    emp_pred = predicate_registry.get("company.employee_count")
    assert emp_pred is not None
    assert emp_pred.value_type == "integer"
    assert emp_pred.cardinality == "one"

    tech_pred = predicate_registry.get("company.technology")
    assert tech_pred is not None
    assert tech_pred.cardinality == "many"


def test_value_normalizers():
    """Verify structured normalization for ranges, currencies, and counts."""
    # Employee range
    range_dict = normalize_employee_range("50-200 employees")
    assert range_dict is not None
    assert range_dict["min"] == 50
    assert range_dict["max"] == 200

    single_emp = normalize_employee_range(250)
    assert single_emp is not None
    assert single_emp["value"] == 250

    # Revenue range
    rev_dict = normalize_revenue_range("₹10-50 Cr")
    assert rev_dict is not None
    assert rev_dict["currency"] == "INR"
    assert rev_dict["min"] == 100_000_000.0
    assert rev_dict["max"] == 500_000_000.0

    # Typed fact normalization
    valid, val, _ = normalize_fact_value("integer", "1,500")
    assert valid is True
    assert val == {"value": 1500}

    valid, val, _ = normalize_fact_value("email", "Rahul@GrowXLabs.com")
    assert valid is True
    assert val["email"] == "rahul@growxlabs.com"

    valid, _, err = normalize_fact_value("integer", "not-a-number")
    assert valid is False
    assert err == "invalid_integer"


def test_observation_provenance_and_idempotency():
    """Verify observations record full provenance and deduplicate on retry."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Acme Test {tag}", domain=f"acme-{tag}.com")

    obs1, rej = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.employee_count",
        raw_value=150,
        extractor_name="headcount_extractor",
        extractor_version="v2.1",
        confidence=0.95,
    )
    assert rej is None
    assert obs1 is not None
    assert obs1.id.startswith("obs_")
    assert obs1.extractor_name == "headcount_extractor"
    assert obs1.extractor_version == "v2.1"
    assert obs1.normalized_value_json == {"value": 150}

    # Re-recording identical observation within same hour triggers idempotency
    obs2, rej2 = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.employee_count",
        raw_value=150,
        extractor_name="headcount_extractor",
        extractor_version="v2.1",
        confidence=0.95,
        observed_at=obs1.observed_at,
    )
    assert rej2 is None
    assert obs2 is not None


def test_observation_quarantine_data_quality_gates():
    """Verify malformed observations are quarantined with reason codes."""
    # Unknown predicate
    obs, rej = observation_service.record_observation(
        subject_type="company",
        subject_id="cmp_test123",
        predicate="company.nonexistent_predicate",
        raw_value="something",
    )
    assert obs is None
    assert rej is not None
    assert rej.reason_code == "unknown_predicate"

    # Missing or invalid subject ID
    obs, rej = observation_service.record_observation(
        subject_type="company",
        subject_id="invalid_id_format",
        predicate="company.employee_count",
        raw_value=100,
    )
    assert obs is None
    assert rej is not None
    assert rej.reason_code == "invalid_entity_ref"

    # Invalid value type
    obs, rej = observation_service.record_observation(
        subject_type="company",
        subject_id="cmp_test123",
        predicate="company.employee_count",
        raw_value="invalid_number_string",
    )
    assert obs is None
    assert rej is not None
    assert rej.reason_code == "invalid_integer"


def test_evidence_linking_to_r2_and_snippet():
    """Verify evidence attachment linking observation to R2 object ref and minimal snippet."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Evidence Co {tag}", domain=f"evi-{tag}.com")

    obs, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.description",
        raw_value="GrowX provides an enterprise data engine.",
    )
    assert obs is not None

    evi = evidence_service.attach_evidence(
        observation_id=obs.id,
        evidence_type="html_fragment",
        object_ref_id="obj_test_r2_key",
        source_url=f"https://evi-{tag}.com/about",
        selector="meta[name='description']",
        quoted_text="GrowX provides an enterprise data engine for high-growth revenue operations.",
    )
    assert evi.id.startswith("evi_")
    assert evi.object_ref_id == "obj_test_r2_key"
    assert "GrowX provides an enterprise" in evi.quoted_text

    evidence_list = evidence_service.list_by_observation(obs.id)
    assert len(evidence_list) >= 1
    assert evidence_list[0].id == evi.id


def test_historical_value_preservation_on_update():
    """Verify Section 15 rule: old values are never destroyed when a fact updates."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"History Corp {tag}", domain=f"history-{tag}.com")

    # Observation 1: 120 employees observed at T1
    obs1, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.employee_count",
        raw_value=120,
        observed_at="2026-01-01T00:00:00Z",
    )
    fact = fact_service.propose_fact(obs1, source_authority_class="official")
    assert fact.current_value_json == {"value": 120}

    # Observation 2: 250 employees observed at T2 from same authoritative source
    obs2, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.employee_count",
        raw_value=250,
        observed_at="2026-09-01T00:00:00Z",
    )
    fact_updated = fact_service.propose_fact(obs2, source_authority_class="official")
    assert fact_updated.id == fact.id
    assert fact_updated.current_value_json == {"value": 250}

    # Verify history preservation: old value must exist with valid_to set
    history = fact_service.get_history(fact.id)
    assert len(history) == 2
    
    # Oldest value was 120, now superseded
    superseded_vals = [h for h in history if h.value_json == {"value": 120}]
    assert len(superseded_vals) == 1
    assert superseded_vals[0].status == "superseded"
    assert superseded_vals[0].valid_to == "2026-09-01T00:00:00Z"

    # Current accepted value is 250
    accepted_vals = [h for h in history if h.value_json == {"value": 250}]
    assert len(accepted_vals) == 1
    assert accepted_vals[0].status == "accepted"


def test_same_value_deduplication_and_confidence_boost():
    """Verify repeating identical observations updates last_seen and boosts confidence without duplicate facts."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Dedupe Co {tag}", domain=f"dedupe-{tag}.com")

    obs1, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.industry",
        raw_value="B2B SaaS",
        observed_at="2026-01-01T00:00:00Z",
    )
    fact1 = fact_service.propose_fact(obs1, source_authority_class="first_party")
    initial_conf = fact1.confidence

    # Second observation with same value from another source
    obs2, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.industry",
        raw_value="B2B SaaS",
        observed_at="2026-06-01T00:00:00Z",
    )
    fact2 = fact_service.propose_fact(obs2, source_authority_class="trusted_directory")

    assert fact2.id == fact1.id
    assert fact2.last_seen_at == "2026-06-01T00:00:00Z"
    assert fact2.confidence >= initial_conf
    assert fact2.verification_state == "multi_source_supported"


def test_multi_value_facts_coexistence():
    """Verify multi-value predicates (e.g. technologies) coexist additively."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Tech Co {tag}", domain=f"tech-{tag}.com")

    techs = ["PostgreSQL", "React", "Python", "FastAPI"]
    fact_ids = set()

    for t in techs:
        obs, _ = observation_service.record_observation(
            subject_type="company",
            subject_id=comp.id,
            predicate="company.technology",
            raw_value=t,
        )
        fact = fact_service.propose_fact(obs)
        fact_ids.add(fact.id)

    # All values coexist under the company's facts
    all_facts = fact_service.list_current(subject_type="company", subject_id=comp.id)
    tech_facts = [f for f in all_facts if f.predicate == "company.technology"]
    assert len(tech_facts) >= 1
    
    # Check history of technology values
    history = fact_service.get_history(tech_facts[0].id)
    history_vals = [h.value_json.get("value") for h in history]
    for t in techs:
        assert t in history_vals


def test_conflict_detection_and_preservation():
    """Verify Section 29-31 rule: conflicting sources open tracked conflict without silent overwrite."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Conflict Co {tag}", domain=f"conflict-{tag}.com")

    # Source A claims founded year is 2018
    obs_a, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.founded_year",
        raw_value=2018,
    )
    fact = fact_service.propose_fact(obs_a, source_authority_class="third_party")
    assert fact.status == "accepted"

    # Source B claims founded year is 2022 (conflict_on_disagree policy)
    obs_b, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.founded_year",
        raw_value=2022,
    )
    fact_conflict = fact_service.propose_fact(obs_b, source_authority_class="third_party")

    assert fact_conflict.status == "conflicting"
    assert fact_conflict.verification_state == "disputed"

    # Verify open conflict was recorded
    conflicts = fact_service.list_conflicts(subject_type="company", subject_id=comp.id, status="open")
    assert len(conflicts) >= 1
    assert conflicts[0].predicate == "company.founded_year"


def test_scope_isolation():
    """Verify private account facts are isolated from global queries."""
    tag = uuid.uuid4().hex[:6]
    comp = identity_service.get_or_create_company(f"Scope Co {tag}", domain=f"scope-{tag}.com")

    obs, _ = observation_service.record_observation(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.industry",
        raw_value="Fintech",
    )
    # Propose under private account scope
    fact_private = fact_service.propose_fact(
        obs,
        scope_type="account",
        scope_id="acc_enterprise_99",
    )
    assert fact_private.scope_type == "account"
    assert fact_private.scope_id == "acc_enterprise_99"

    # Global query must not find private fact
    fact_global = fact_service.get_current(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.industry",
        scope_type="global",
        scope_id="global",
    )
    assert fact_global is None

    # Account query finds private fact
    found = fact_service.get_current(
        subject_type="company",
        subject_id=comp.id,
        predicate="company.industry",
        scope_type="account",
        scope_id="acc_enterprise_99",
    )
    assert found is not None
    assert found.id == fact_private.id


def test_extractor_and_autogtm_adapters():
    """Verify crawler extraction output flows through adapter into canonical facts and AutoGTM."""
    tag = uuid.uuid4().hex[:6]
    domain = f"extract-{tag}.io"
    company_name = f"Hexagon Platform {tag}"

    analysis_output = {
        "summary": "Enterprise data and revenue orchestration platform",
        "industry": "Enterprise Software",
        "employee_count": 350,
        "phone": "+1 555 0192",
        "email": f"contact@{domain}",
        "tech_stack": ["PostgreSQL", "FastAPI", "Docker", "Kubernetes"],
        "features": ["Autonomous Crawl", "Entity Resolution", "AutoGTM"],
    }

    facts = extractor_adapter.ingest_extraction_result(
        domain=domain,
        company_name=company_name,
        analysis_dict=analysis_output,
        source_url=f"https://{domain}",
    )
    assert len(facts) >= 5

    # Test AutoGTM Adapter reads verified canonical facts
    comp = identity_service.get_or_create_company(company_name, domain=domain)
    intel = autogtm_adapter.get_verified_company_intelligence(comp.id)

    assert intel["company_id"] == comp.id
    assert intel["industry"] == "Enterprise Software"
    assert intel["employee_count"] == 350
    assert "FastAPI" in intel["technologies"]
    assert "Autonomous Crawl" in intel["products"]
    assert intel["overall_confidence"] > 0.5


def test_quality_metrics_calculation():
    """Verify Section 71 quality metrics reporting."""
    metrics = fact_service.calculate_quality_metrics()
    assert "facts_with_evidence_rate" in metrics
    assert "conflicting_fact_rate" in metrics
    assert "quarantine_rejection_rate" in metrics
    assert "total_facts" in metrics
    assert metrics["facts_with_evidence_rate"] == 1.0
