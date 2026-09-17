import logging
import os
from typing import Optional
import httpx
from growx_crawl.autogtm.models import CompanyAnalysis, OutreachSequence, ProspectLead

logger = logging.getLogger("growx_crawl.autogtm.copywriter")


class MultiChannelCopywriter:
    """
    Generates high-converting multi-channel sales copy grounded in live crawled facts.
    Applies the Josh Braun 'Poke' framework and Alex Hormozi Value Equation.
    Zero generic AI fluff.
    """

    def generate_heuristic_sequence(
        self,
        lead: ProspectLead,
        sender: CompanyAnalysis,
    ) -> OutreachSequence:
        p_name = lead.first_name or "there"
        p_comp = lead.company_name
        p_role = lead.title
        s_comp = sender.company_name
        s_offer = sender.primary_offer
        hook = lead.personalization_hook or f"noted {p_comp}'s recent market expansion"

        # 1. Primary Cold Email
        subject = f"quick question re {p_comp}"
        body = (
            f"Hi {p_name},\n\n"
            f"Saw that {hook} — really sharp execution.\n\n"
            f"Most {p_role}s we speak with mentioned that scaling outbound pipeline without burning domain reputation or relying on stale databases is their biggest operational friction right now.\n\n"
            f"At {s_comp}, we built {s_offer} to autonomously crawl, verify, and generate hyper-targeted sales pipeline with zero bounce guarantee.\n\n"
            f"Put together a quick 3-minute custom pipeline teardown for {p_comp} showing 15 verified accounts ready to contact.\n\n"
            f"Open to taking a look?\n\n"
            f"Best,\n"
            f"GrowX Labs Growth Team"
        )

        # 2. Follow-Up 1 (Day 3 Value Add)
        followup_1 = (
            f"Hi {p_name},\n\n"
            f"Quick follow-up on my note below regarding {p_comp}.\n\n"
            f"Ran a quick test crawl across your target buyer profile and identified 3 key buying signals that standard databases like Apollo miss (recent team page additions + live hiring signals).\n\n"
            f"Happy to send over the raw spreadsheet if helpful — no pitch needed.\n\n"
            f"Best,\n"
            f"GrowX Labs"
        )

        # 3. Follow-Up 2 (Day 7 Polite Break-up)
        followup_2 = (
            f"Hi {p_name},\n\n"
            f"Assuming outbound pipeline automation isn't a priority for {p_comp} right now. Totally understand!\n\n"
            f"I won't clutter your inbox further. If priorities shift later this quarter, feel free to reach back out.\n\n"
            f"Wishing you and {p_comp} continued momentum.\n\n"
            f"Best,\n"
            f"GrowX Labs"
        )

        # 4. LinkedIn Connection Note (< 300 characters)
        linkedin_note = (
            f"Hi {p_name}, saw your work heading up {p_comp}. Loved seeing {hook[:60]}. "
            f"Always keen to connect with leaders in your space — let's stay in touch!"
        )[:295]

        # 5. Twitter / X DM
        twitter_dm = (
            f"Hey {p_name} — caught {p_comp}'s recent updates. "
            f"Put together a quick live teardown on your outbound ICP that might save you 10+ hrs this month. Mind if I drop a link?"
        )

        return OutreachSequence(
            email_subject=subject,
            email_body=body,
            email_followup_1=followup_1,
            email_followup_2=followup_2,
            linkedin_note=linkedin_note,
            twitter_dm=twitter_dm,
        )

    async def generate_outreach(
        self,
        lead: ProspectLead,
        sender: CompanyAnalysis,
    ) -> OutreachSequence:
        """
        Generates personalized multi-channel copy using GrowX AI Gateway,
        falling back to battle-tested heuristics on failure.
        """
        from growx_crawl.ai.gateway import ai_gateway
        from growx_crawl.ai.models import StructuredAIRequest

        prompt = f"""
You are an elite B2B sales copywriter trained on Josh Braun, Chris Voss, and Alex Hormozi.
Write a 3-step cold email sequence and LinkedIn note for this prospect:
- Prospect: {lead.name} ({lead.title} at {lead.company_name}, {lead.company_domain})
- Live Crawled Fact / Hook: {lead.personalization_hook}
- Sender: {sender.company_name} ({sender.value_proposition})

RULES:
1. No cheesy spam words ("synergy", "game changer", "hope this email finds you well").
2. Subject must be short, lowercase, and curiosity-based (3-5 words).
3. The email body must cite the crawled fact in line 1.
4. Call to action must be low-friction (interest-based, e.g. "Worth a look?").

Return strictly valid JSON with keys: email_subject, email_body, email_followup_1, email_followup_2, linkedin_note, twitter_dm.
"""
        req = StructuredAIRequest(
            task="email_personalization",
            prompt=prompt,
            schema_class=OutreachSequence,
            metadata_json={"lead_id": lead.id, "company": lead.company_name},
        )

        try:
            res = await ai_gateway.generate_structured(req)
            if res.structured_output:
                data = res.structured_output
                return OutreachSequence(
                    email_subject=data.get("email_subject", f"quick question re {lead.company_name}"),
                    email_body=data.get("email_body", ""),
                    email_followup_1=data.get("email_followup_1", ""),
                    email_followup_2=data.get("email_followup_2", ""),
                    linkedin_note=data.get("linkedin_note", "")[:295],
                    twitter_dm=data.get("twitter_dm", ""),
                )
        except Exception as e:
            logger.warning(f"AI Gateway copywriting failed, falling back to heuristic: {e}")

        return self.generate_heuristic_sequence(lead, sender)


multi_channel_copywriter = MultiChannelCopywriter()
