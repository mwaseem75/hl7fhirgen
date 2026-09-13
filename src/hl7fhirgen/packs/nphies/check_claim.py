"""Pre-submission claim checking: generic profile validation plus rejection-pattern
cross-referencing for any `error[].code` (or similarly-shaped) codings already present
on a resource, e.g. from a payer's ClaimResponse.
"""
from __future__ import annotations

from hl7fhirgen.packs.nphies.rejection_codes import RejectionExplanation, explain_rejection
from hl7fhirgen.structure_definition import StructureDefinition
from hl7fhirgen.validator import ValidationResult, validate_resource


def check_claim(resource: dict, sd: StructureDefinition) -> tuple[ValidationResult, list[RejectionExplanation]]:
    """Validate `resource` against `sd`, and explain any recognized rejection codes.

    Args:
        resource: A Claim, ClaimResponse, or CoverageEligibilityResponse-shaped resource.
        sd: The profile to validate against (your own, e.g. a downloaded NPHIES profile).

    Returns:
        A tuple of (ValidationResult from the generic validator, a list of
        RejectionExplanation for every code found under `error[].code.coding[].code`
        that's recognized in the bundled knowledge base — see
        `hl7fhirgen.packs.nphies.rejection_codes` for what "recognized" means).
    """
    result = validate_resource(resource, sd)

    explanations = []
    for error in resource.get("error", []) or []:
        for coding in ((error.get("code") or {}).get("coding") or []):
            code = coding.get("code")
            explanation = explain_rejection(code) if code else None
            if explanation:
                explanations.append(explanation)

    return result, explanations
