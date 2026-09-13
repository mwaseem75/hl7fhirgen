"""NPHIES pack: tooling for Saudi Arabia's national FHIR claims/eligibility exchange.

IMPORTANT — read this before relying on any part of this pack for a real claim:

- The rejection-code knowledge base in `rejection_codes.py` ships with a small set of
  ILLUSTRATIVE EXAMPLE entries seeding its structure. It is a community-maintained
  lookup table, not an official mirror of NPHIES's terminology — hl7fhirgen has no
  live feed of NPHIES's actual CodeSystem. See `rejection_codes.DISCLAIMER`.
- `check_claim` validates a resource against whatever StructureDefinition *you* supply
  (e.g. your own copy of a real NPHIES profile downloaded from the NPHIES developer
  portal) using the same generic, documented-subset validator as the rest of
  hl7fhirgen — see the top-level README "Scope" section for exactly what that checks.
- Nothing in this pack was built from, or contains, non-public NPHIES material.

Contributions of real, encountered rejection codes (with enough context to describe
the general pattern, not any patient- or claim-identifying detail) are very welcome —
see CONTRIBUTING.md.
"""
from hl7fhirgen.packs.nphies.check_claim import check_claim
from hl7fhirgen.packs.nphies.rejection_codes import DISCLAIMER, RejectionExplanation, explain_rejection, list_rejection_codes

__all__ = [
    "DISCLAIMER",
    "RejectionExplanation",
    "check_claim",
    "explain_rejection",
    "list_rejection_codes",
]
