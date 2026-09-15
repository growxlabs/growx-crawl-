from typing import List, Tuple
from growx_crawl.integrations.dto import GrowXLabsLeadPayload


class PayloadValidator:
    @classmethod
    def validate_lead(cls, lead: GrowXLabsLeadPayload) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not lead.company_name or len(lead.company_name.strip()) == 0:
            errors.append("company_name is required and cannot be empty")

        if not (0 <= lead.lead_score <= 100):
            errors.append(f"lead_score must be between 0 and 100, got {lead.lead_score}")

        if lead.priority not in ["High", "Medium", "Low", "review"]:
            errors.append(f"Invalid priority string: {lead.priority}")

        if lead.website and not (lead.website.startswith("http://") or lead.website.startswith("https://")):
            errors.append(f"website URL must start with http:// or https://, got {lead.website}")

        return (len(errors) == 0, errors)

    @classmethod
    def validate_batch(cls, leads: List[GrowXLabsLeadPayload]) -> Tuple[List[GrowXLabsLeadPayload], List[Tuple[GrowXLabsLeadPayload, List[str]]]]:
        valid_leads: List[GrowXLabsLeadPayload] = []
        invalid_leads: List[Tuple[GrowXLabsLeadPayload, List[str]]] = []

        for lead in leads:
            is_valid, errs = cls.validate_lead(lead)
            if is_valid:
                valid_leads.append(lead)
            else:
                invalid_leads.append((lead, errs))

        return valid_leads, invalid_leads
