"""
GrowX Golden AI Benchmark Datasets & Schemas.
Used for evaluation harness and prompt regression testing.
"""

from typing import List, Optional
from pydantic import BaseModel


class CompanyAnalysisSchema(BaseModel):
    company_name: str
    tagline: str
    summary: str
    primary_offer: str
    value_proposition: str
    target_audience: List[str]
    features: List[str]
    pricing_model: str


class ICPProfileSchema(BaseModel):
    target_industries: List[str]
    company_size: List[str]
    target_roles: List[str]
    pain_points: List[str]


class OutreachSequenceSchema(BaseModel):
    email_subject: str
    email_body: str
    email_followup_1: str
    email_followup_2: str
    linkedin_note: str
    twitter_dm: str


class VerificationReasoningSchema(BaseModel):
    assessment: str
    confidence: float
    reasoning: str
    recommendation: str


GOLDEN_COMPANY_ANALYSIS_BENCHMARK = [
    {
        "id": "case_stripe",
        "prompt": "Analyze Stripe website data",
        "input_vars": {
            "domain": "stripe.com",
            "content": "Stripe is a financial infrastructure platform for the internet. Millions of companies use Stripe software to accept payments.",
        },
        "schema_class": CompanyAnalysisSchema,
        "required_fields": ["company_name", "primary_offer", "value_proposition", "target_audience"],
    },
    {
        "id": "case_growx",
        "prompt": "Analyze GrowX website data",
        "input_vars": {
            "domain": "growxlabs.com",
            "content": "GrowX Labs provides autonomous B2B crawling, real-time verification, and AutoGTM sales pipeline generation.",
        },
        "schema_class": CompanyAnalysisSchema,
        "required_fields": ["company_name", "primary_offer", "value_proposition"],
    },
]

GOLDEN_ICP_BENCHMARK = [
    {
        "id": "case_icp_fintech",
        "prompt": "Synthesize ICP for fintech infrastructure",
        "input_vars": {
            "company_name": "PayStream",
            "domain": "paystream.io",
            "primary_offer": "Real-time payment routing engine",
            "value_proposition": "Cut payment processing fees by 30%",
            "summary": "High-throughput API for merchant payment aggregation",
        },
        "schema_class": ICPProfileSchema,
        "required_fields": ["target_industries", "company_size", "target_roles", "pain_points"],
    }
]

GOLDEN_EMAIL_BENCHMARK = [
    {
        "id": "case_email_sdr",
        "prompt": "Write cold outreach for VP of Sales",
        "input_vars": {
            "lead_name": "Sarah Connor",
            "title": "VP of Sales",
            "company_name": "Cyberdyne Systems",
            "company_domain": "cyberdyne.com",
            "hook": "Recent Series B expansion into cloud security",
            "sender_offer": "Autonomous sales prospector",
            "sender_value_prop": "Generate 50 verified qualified meetings/month",
        },
        "schema_class": OutreachSequenceSchema,
        "required_fields": ["email_subject", "email_body", "email_followup_1", "linkedin_note"],
    }
]
