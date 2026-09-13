import json
from pathlib import Path

from hl7fhirgen.generator import generate_resource
from hl7fhirgen.packs.nphies import check_claim, explain_rejection, list_rejection_codes
from hl7fhirgen.structure_definition import load_structure_definition
from hl7fhirgen.validator import validate_resource

NPHIES_EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "nphies"


def test_claim_example_profile_generates_and_validates_clean():
    sd = load_structure_definition(str(NPHIES_EXAMPLES / "claim-example-profile.json"))
    resource = generate_resource(sd, include_optional=True)

    assert resource["resourceType"] == "Claim"
    assert resource["status"] == "active"
    assert resource["use"] == "claim"
    assert resource["diagnosis"][0]["diagnosisCodeableConcept"]
    assert resource["item"][0]["productOrService"]

    result = validate_resource(resource, sd)
    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]


def test_explain_rejection_known_code():
    explanation = explain_rejection("duplicate-claim")
    assert explanation is not None
    assert explanation.suggested_fix


def test_explain_rejection_unknown_code_returns_none():
    assert explain_rejection("not-a-real-code") is None


def test_list_rejection_codes_includes_seeded_examples():
    codes = list_rejection_codes()
    assert "duplicate-claim" in codes
    assert "missing-preauth" in codes


def test_check_claim_cross_references_rejection_codes():
    sd = load_structure_definition(str(NPHIES_EXAMPLES / "claim-response-example-profile.json"))
    resource = json.loads((NPHIES_EXAMPLES / "claim-response-example.json").read_text(encoding="utf-8"))

    result, explanations = check_claim(resource, sd)

    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]
    codes_found = {e.code for e in explanations}
    assert codes_found == {"duplicate-claim", "missing-preauth"}
