"""
GrowX AutoGTM Email Verifier Adapter.
Compatibility adapter forwarding all verification calls to growx_crawl.verification.email.
Maintains 100% backward compatibility for existing callers.
"""

from growx_crawl.verification.email import EMAIL_REGEX, EmailVerifier, email_verifier

__all__ = [
    "EMAIL_REGEX",
    "EmailVerifier",
    "email_verifier",
]
