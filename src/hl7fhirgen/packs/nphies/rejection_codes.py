"""A community-editable knowledge base of FHIR claim/eligibility rejection patterns.

Keys are descriptive slugs (not official NPHIES code identifiers) so this table
can't be mistaken for an authoritative enumeration of NPHIES's actual terminology —
see the module-level disclaimer below and `hl7fhirgen.packs.nphies`'s docstring.
"""
from __future__ import annotations

from dataclasses import dataclass

DISCLAIMER = (
    "Community-sourced guidance seeded with illustrative examples, not an official "
    "NPHIES source. Verify against the current NPHIES Implementation Guide and your "
    "payer contract before acting on a real claim decision."
)


@dataclass
class RejectionExplanation:
    """One entry in the rejection-code knowledge base.

    Attributes:
        code: The lookup key used with `explain_rejection` (a descriptive slug).
        title: A one-line, plain-English summary of what went wrong.
        likely_causes: Common reasons this pattern shows up in practice.
        suggested_fix: What to check or do before resubmitting.
    """

    code: str
    title: str
    likely_causes: list[str]
    suggested_fix: str


REJECTION_CODES: dict[str, RejectionExplanation] = {
    "eligibility-expired": RejectionExplanation(
        code="eligibility-expired",
        title="Patient eligibility does not cover the service date",
        likely_causes=[
            "Eligibility was checked before the service date and coverage changed or lapsed since",
            "The policy end date on file predates the claim's service date",
        ],
        suggested_fix="Re-run an eligibility check for the actual service date before resubmitting; "
                       "if coverage has genuinely lapsed, confirm the current policy status with the payer.",
    ),
    "missing-preauth": RejectionExplanation(
        code="missing-preauth",
        title="A required pre-authorization was not obtained or referenced",
        likely_causes=[
            "The service/procedure requires prior authorization under the patient's plan",
            "A pre-authorization exists but wasn't referenced on the claim",
        ],
        suggested_fix="Confirm whether the billed service requires pre-auth for this plan; if a prior "
                       "authorization exists, include its reference on resubmission, otherwise request one first.",
    ),
    "diagnosis-not-covered": RejectionExplanation(
        code="diagnosis-not-covered",
        title="The diagnosis on the claim is not covered under the patient's plan",
        likely_causes=[
            "The diagnosis code maps to an excluded condition or category for this plan",
            "A more specific or different diagnosis code should have been used",
        ],
        suggested_fix="Check the coded diagnosis against the plan's exclusions and confirm it's the most "
                       "clinically accurate and specific code available before resubmitting.",
    ),
    "duplicate-claim": RejectionExplanation(
        code="duplicate-claim",
        title="A claim for this patient/service/date appears to already be on file",
        likely_causes=[
            "The claim was already submitted and is still processing",
            "A resubmission was sent without referencing the original claim",
        ],
        suggested_fix="Check claim status before resubmitting; if correcting an earlier claim, reference "
                       "it explicitly rather than submitting a fresh one.",
    ),
    "invalid-provider-id": RejectionExplanation(
        code="invalid-provider-id",
        title="The billing or rendering provider identifier could not be matched",
        likely_causes=[
            "A typo or outdated identifier for the provider/facility",
            "The provider is not registered/active for this payer or service type",
        ],
        suggested_fix="Verify the provider identifier against the payer's current registry and confirm "
                       "the provider is active for the billed service type.",
    ),
}


def explain_rejection(code: str) -> RejectionExplanation | None:
    """Look up a rejection pattern by its slug. Returns None if not in the knowledge base."""
    return REJECTION_CODES.get(code)


def list_rejection_codes() -> list[str]:
    """All known rejection-pattern slugs, sorted."""
    return sorted(REJECTION_CODES)
