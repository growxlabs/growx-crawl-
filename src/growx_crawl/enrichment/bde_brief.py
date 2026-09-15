from typing import Any, Dict, List
from growx_crawl.models.enrichment import BDELeadBrief
from growx_crawl.models.lead import Company


class BDEBriefGenerator:
    @classmethod
    def generate_brief(cls, company: Company, scoring_data: Dict[str, Any] = None) -> BDELeadBrief:
        emails = company.emails
        phones = company.phones
        socials = company.social_profiles
        contacts = company.contacts

        primary_phone = phones[0].phone if phones else None
        primary_email = emails[0].email if emails else None
        whatsapp = next((p.phone for p in phones if "whatsapp" in p.raw_phone.lower()), None)
        if not whatsapp and primary_phone:
            whatsapp = primary_phone

        ig = next((s.url for s in socials if s.platform == "instagram"), None)
        li = next((s.url for s in socials if s.platform == "linkedin"), None)
        fb = next((s.url for s in socials if s.platform == "facebook"), None)

        # Primary decision maker selection rule: Tier 1 > Tier 2 > Tier 3 > first contact
        primary_dm = None
        dm_role = None
        dm_tier = None
        dm_conf = 0.0

        if contacts:
            sorted_contacts = sorted(
                contacts,
                key=lambda c: 1 if c.decision_maker_tier == "Tier 1" else (2 if c.decision_maker_tier == "Tier 2" else 3),
            )
            top_dm = sorted_contacts[0]
            primary_dm = top_dm.name
            dm_role = top_dm.title
            dm_tier = top_dm.decision_maker_tier or "Tier 3"
            dm_conf = top_dm.confidence

        # Deterministic summary generation
        summary_parts = []
        summary_parts.append(f"{company.name} is a {company.industry or 'business'} prospect in {company.city or 'India'}.")

        if company.website_missing:
            summary_parts.append("Website is not listed; business identity discovered via local directory/maps.")
        else:
            summary_parts.append(f"Official website: {company.website}.")

        if primary_phone:
            summary_parts.append(f"Primary phone: {primary_phone}.")
        if primary_email:
            summary_parts.append(f"Public email: {primary_email}.")

        if ig:
            summary_parts.append("Instagram presence verified.")

        if primary_dm:
            summary_parts.append(f"Key decision maker: {primary_dm} ({dm_role}).")
        else:
            summary_parts.append("No public leadership contact was identified on the website.")

        research_summary = " ".join(summary_parts)

        # Prospect flags
        flags: List[str] = []
        if company.website_missing:
            flags.append("no_website")
        if not primary_email:
            flags.append("missing_email")
        if not primary_phone:
            flags.append("missing_phone")
        if not primary_dm:
            flags.append("missing_decision_maker")
        if whatsapp:
            flags.append("whatsapp_available")

        return BDELeadBrief(
            company_name=company.name,
            industry=company.industry,
            category=company.category,
            city=company.city,
            state=company.state,
            country=company.country,
            website=company.website,
            website_missing=company.website_missing,
            description=company.description,
            primary_phone=primary_phone,
            primary_email=primary_email,
            whatsapp=whatsapp,
            instagram=ig,
            linkedin=li,
            facebook=fb,
            primary_decision_maker=primary_dm,
            decision_maker_role=dm_role,
            decision_maker_tier=dm_tier,
            decision_maker_confidence=dm_conf,
            products_services=[company.industry] if company.industry else [],
            prospect_flags=flags,
            research_summary=research_summary,
            source=company.source,
            source_url=company.source_url,
            confidence=company.confidence,
        )
