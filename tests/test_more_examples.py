"""Round-trip tests for the additional bundled example profiles (Observation,
Encounter) — beyond Patient and the NPHIES pack's Claim/ClaimResponse — chosen to
exercise choice types on a non-Patient resource (Observation.effective[x]/value[x])
and a repeating BackboneElement with a nested required Reference (Encounter.participant).
"""
from pathlib import Path

from hl7fhirgen.generator import generate_resource
from hl7fhirgen.structure_definition import load_structure_definition
from hl7fhirgen.validator import validate_resource

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_observation_example_generates_and_validates_clean():
    sd = load_structure_definition(str(EXAMPLES_DIR / "observation-example-profile.json"))
    resource = generate_resource(sd, include_optional=True)

    assert resource["resourceType"] == "Observation"
    assert resource["status"] == "final"
    assert "effectiveDateTime" in resource
    assert "valueQuantity" in resource

    result = validate_resource(resource, sd)
    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]


def test_encounter_example_generates_and_validates_clean():
    sd = load_structure_definition(str(EXAMPLES_DIR / "encounter-example-profile.json"))
    resource = generate_resource(sd, include_optional=True)

    assert resource["resourceType"] == "Encounter"
    assert resource["status"] == "finished"
    assert resource["participant"][0]["individual"]["reference"].startswith("Practitioner/")

    result = validate_resource(resource, sd)
    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]


def test_encounter_reason_code_only_included_with_full():
    sd = load_structure_definition(str(EXAMPLES_DIR / "encounter-example-profile.json"))
    minimal = generate_resource(sd, include_optional=False)
    full = generate_resource(sd, include_optional=True)
    assert "reasonCode" not in minimal
    assert "reasonCode" in full
