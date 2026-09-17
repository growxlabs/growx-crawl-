from typing import Dict, Optional
from growx_crawl.intelligence.facts.models import FactPredicateEntity

STANDARD_PREDICATES: Dict[str, FactPredicateEntity] = {
    # Company Predicates
    "company.legal_name": FactPredicateEntity(
        predicate="company.legal_name",
        subject_type="company",
        value_type="string",
        cardinality="one",
        verification_policy="strict",
        freshness_policy="365d",
        merge_policy="latest_wins",
        description="Official registered legal name of the company",
    ),
    "company.industry": FactPredicateEntity(
        predicate="company.industry",
        subject_type="company",
        value_type="string",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="latest_wins",
        description="Primary industry classification",
    ),
    "company.employee_count": FactPredicateEntity(
        predicate="company.employee_count",
        subject_type="company",
        value_type="integer",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="latest_wins",
        description="Exact observed employee headcount",
    ),
    "company.employee_range": FactPredicateEntity(
        predicate="company.employee_range",
        subject_type="company",
        value_type="json",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="latest_wins",
        description="Structured headcount range (min, max, unit)",
    ),
    "company.revenue_range": FactPredicateEntity(
        predicate="company.revenue_range",
        subject_type="company",
        value_type="json",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="conflict_on_disagree",
        description="Structured annual revenue range (min, max, currency, period)",
    ),
    "company.headquarters": FactPredicateEntity(
        predicate="company.headquarters",
        subject_type="company",
        value_type="entity_ref",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="365d",
        merge_policy="latest_wins",
        description="Reference to canonical primary location entity (loc_...)",
    ),
    "company.founded_year": FactPredicateEntity(
        predicate="company.founded_year",
        subject_type="company",
        value_type="integer",
        cardinality="one",
        verification_policy="strict",
        freshness_policy="3650d",
        merge_policy="conflict_on_disagree",
        description="Year the company was founded",
    ),
    "company.description": FactPredicateEntity(
        predicate="company.description",
        subject_type="company",
        value_type="string",
        cardinality="one",
        verification_policy="relaxed",
        freshness_policy="180d",
        merge_policy="latest_wins",
        description="Canonical business description or value proposition",
    ),
    "company.phone": FactPredicateEntity(
        predicate="company.phone",
        subject_type="company",
        value_type="phone",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="latest_wins",
        description="Primary corporate telephone number",
    ),
    "company.email": FactPredicateEntity(
        predicate="company.email",
        subject_type="company",
        value_type="email",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="latest_wins",
        description="Primary corporate contact email",
    ),
    "company.erp": FactPredicateEntity(
        predicate="company.erp",
        subject_type="company",
        value_type="string",
        cardinality="many",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="additive",
        description="Enterprise Resource Planning systems in use",
    ),
    "company.crm": FactPredicateEntity(
        predicate="company.crm",
        subject_type="company",
        value_type="string",
        cardinality="many",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="additive",
        description="Customer Relationship Management systems in use",
    ),
    "company.accounting_software": FactPredicateEntity(
        predicate="company.accounting_software",
        subject_type="company",
        value_type="string",
        cardinality="many",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="additive",
        description="Accounting and finance software in use",
    ),
    "company.technology": FactPredicateEntity(
        predicate="company.technology",
        subject_type="company",
        value_type="string",
        cardinality="many",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="additive",
        description="Technologies, libraries, and frameworks detected in tech stack",
    ),
    "company.product": FactPredicateEntity(
        predicate="company.product",
        subject_type="company",
        value_type="string",
        cardinality="many",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="additive",
        description="Products offered by the company",
    ),
    "company.service": FactPredicateEntity(
        predicate="company.service",
        subject_type="company",
        value_type="string",
        cardinality="many",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="additive",
        description="Services offered by the company",
    ),

    # Person Predicates
    "person.title": FactPredicateEntity(
        predicate="person.title",
        subject_type="person",
        value_type="string",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="latest_wins",
        description="Current professional job title",
    ),
    "person.department": FactPredicateEntity(
        predicate="person.department",
        subject_type="person",
        value_type="string",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="latest_wins",
        description="Functional department (e.g. Engineering, Sales, Finance)",
    ),
    "person.seniority": FactPredicateEntity(
        predicate="person.seniority",
        subject_type="person",
        value_type="string",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="latest_wins",
        description="Seniority level (e.g. C-Level, VP, Director, Manager, IC)",
    ),
    "person.location": FactPredicateEntity(
        predicate="person.location",
        subject_type="person",
        value_type="string",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="180d",
        merge_policy="latest_wins",
        description="Geographic location text of the person",
    ),
    "person.current_company": FactPredicateEntity(
        predicate="person.current_company",
        subject_type="person",
        value_type="entity_ref",
        cardinality="one",
        verification_policy="standard",
        freshness_policy="90d",
        merge_policy="latest_wins",
        description="Reference to canonical company entity (cmp_...)",
    ),
    "person.work_email": FactPredicateEntity(
        predicate="person.work_email",
        subject_type="person",
        value_type="email",
        cardinality="one",
        verification_policy="strict",
        freshness_policy="30d",
        merge_policy="latest_wins",
        description="Verified corporate work email address",
    ),
}


class PredicateRegistry:
    """
    Registry enforcing controlled, typed predicate declarations across GrowX.
    """

    def __init__(self, predicates: Optional[Dict[str, FactPredicateEntity]] = None):
        self._predicates: Dict[str, FactPredicateEntity] = dict(predicates or STANDARD_PREDICATES)

    def get(self, predicate: str) -> Optional[FactPredicateEntity]:
        return self._predicates.get(predicate)

    def register(self, predicate_entity: FactPredicateEntity) -> None:
        self._predicates[predicate_entity.predicate] = predicate_entity

    def is_known(self, predicate: str) -> bool:
        return predicate in self._predicates

    def list_all(self) -> Dict[str, FactPredicateEntity]:
        return dict(self._predicates)


predicate_registry = PredicateRegistry()
