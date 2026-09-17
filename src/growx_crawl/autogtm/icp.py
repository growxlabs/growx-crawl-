import logging
from typing import List
from growx_crawl.autogtm.models import CompanyAnalysis, ICPProfile

logger = logging.getLogger("growx_crawl.autogtm.icp")


class ICPSynthesizer:
    """
    Synthesizes the Ideal Customer Profile (ICP) based on deep domain analysis,
    generating high-conversion target titles, industries, pain points, and search dorks.
    """

    def synthesize(self, analysis: CompanyAnalysis) -> ICPProfile:
        domain = analysis.domain
        offer = analysis.primary_offer.lower()
        val_prop = analysis.value_proposition.lower()
        summary = analysis.summary.lower()
        audiences = analysis.target_audience

        # 1. Target Industries
        industries: List[str] = []
        if any(w in offer or w in val_prop or w in summary for w in ["lead", "sales", "outreach", "pipeline", "crawl", "growth"]):
            industries.extend(["B2B SaaS & Cloud Software", "Growth & Marketing Agencies", "Staffing & Recruiting", "IT & Cybersecurity Services"])
        elif any(w in offer or w in val_prop for w in ["store", "ecommerce", "shop", "retail", "brand"]):
            industries.extend(["eCommerce & D2C Brands", "Fashion & Apparel", "Consumer Packaged Goods (CPG)", "Retail Tech"])
        elif any(w in offer or w in val_prop for w in ["health", "clinic", "patient", "medical"]):
            industries.extend(["Digital Health & MedTech", "Healthcare Providers", "Biotech & Pharmaceuticals"])
        elif any(w in offer or w in val_prop for w in ["fintech", "payment", "bank", "invest", "crypto"]):
            industries.extend(["Fintech & Financial Services", "Wealth Management", "InsurTech", "Accounting Firms"])
        else:
            industries.extend(["B2B Technology Companies", "Digital Professional Services", "Growth-Stage Startups", "Mid-Market Enterprises"])

        # 2. Target Roles (Decision Makers)
        roles: List[str] = []
        if any(w in offer or w in val_prop for w in ["lead", "sales", "revenue", "pipeline", "gtm"]):
            roles.extend(["Founder & CEO", "VP of Sales", "Head of Growth", "Chief Revenue Officer (CRO)", "Director of Business Development"])
        elif any(w in offer or w in val_prop for w in ["dev", "code", "infra", "api", "tech", "crawler"]):
            roles.extend(["Chief Technology Officer (CTO)", "VP of Engineering", "Head of Product", "Technical Co-Founder", "Lead Architect"])
        elif any(w in offer or w in val_prop for w in ["market", "content", "seo", "brand", "agency"]):
            roles.extend(["Chief Marketing Officer (CMO)", "Head of Performance Marketing", "VP of Growth Marketing", "Agency Owner / Partner"])
        else:
            roles.extend(["Chief Executive Officer", "Founder", "Managing Director", "Head of Business Operations"])

        # 3. Company Sizes
        company_size = ["11-50 employees (Agile Scaleups)", "51-200 employees (High-Growth Mid-Market)", "201-500 employees (Established Enterprises)"]

        # 4. Geographies
        geographies = ["United States", "United Kingdom", "Canada", "Australia", "Western Europe", "Singapore"]

        # 5. Emotional Buying Triggers & Pain Points
        pain_points: List[str] = [
            f"Struggling with inconsistent inbound pipeline and high customer acquisition costs (CAC).",
            f"Wasting 20+ hours per week manually searching for verified decision-makers and drafting cold pitches.",
            f"High email bounce rates burning domain sender reputation with generic outreach templates.",
            f"Difficulty scaling qualified sales conversations without hiring expensive internal SDR teams.",
        ]

        # 6. Trigger Events (When prospects are most receptive)
        trigger_events: List[str] = [
            "Recently announced new funding or seed/Series A investment round.",
            "Actively hiring for Sales Development Representatives (SDRs) or Account Executives.",
            "Launched a new product, updated pricing page, or expanded into a new market.",
            "Recent executive leadership transition or new VP of Marketing hire.",
        ]

        # 7. Formulated Search Dorks (Live Web Harvesting Queries)
        search_dorks: List[str] = [
            f'site:linkedin.com/in/ ("Founder" OR "CEO") "{industries[0]}"',
            f'site:linkedin.com/in/ ("VP of Sales" OR "Head of Growth") "{industries[0]}"',
            f'site:linkedin.com/in/ ("Chief Revenue Officer") "{industries[1] if len(industries) > 1 else industries[0]}"',
            f'"{industries[0]}" "our team" OR "contact us" "USA"',
        ]

        return ICPProfile(
            target_industries=industries[:4],
            company_size=company_size,
            target_roles=roles[:5],
            geographies=geographies,
            pain_points=pain_points,
            trigger_events=trigger_events,
            search_dorks=search_dorks,
        )


icp_synthesizer = ICPSynthesizer()
