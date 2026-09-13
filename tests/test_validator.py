import copy

from hl7fhirgen.generator import generate_resource
from hl7fhirgen.structure_definition import StructureDefinition
from hl7fhirgen.validator import validate_resource

# Regression fixture for a bug where cardinality was checked by flattening every
# instance of a repeating parent together, instead of per-instance: a resource
# with two "item" entries, each with exactly one "code" (its own 0..1 limit),
# was wrongly flagged as "item.code max cardinality 1 exceeded (found 2)".
REPEATING_PARENT_SD = {
    "resourceType": "StructureDefinition",
    "name": "ExampleBasic",
    "type": "Basic",
    "status": "draft",
    "snapshot": {
        "element": [
            {"id": "Basic", "path": "Basic", "min": 0, "max": "*"},
            {"id": "Basic.item", "path": "Basic.item", "min": 0, "max": "*",
             "type": [{"code": "BackboneElement"}]},
            {"id": "Basic.item.code", "path": "Basic.item.code", "min": 0, "max": "1",
             "type": [{"code": "string"}]},
        ]
    },
}


def test_generated_resource_validates_clean(patient_sd):
    resource = generate_resource(patient_sd, include_optional=True)
    result = validate_resource(resource, patient_sd)
    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]


def test_missing_required_field_is_reported(patient_sd):
    resource = generate_resource(patient_sd)
    del resource["gender"]
    result = validate_resource(resource, patient_sd)
    assert not result.valid
    assert any(i.path == "gender" for i in result.issues)


def test_fixed_value_mismatch_is_reported(patient_sd):
    resource = generate_resource(patient_sd)
    resource["identifier"][0]["system"] = "http://wrong.example.org"
    result = validate_resource(resource, patient_sd)
    assert not result.valid
    assert any(i.path == "identifier.system" for i in result.issues)


def test_invalid_binding_value_is_reported(patient_sd):
    resource = generate_resource(patient_sd)
    resource["gender"] = "not-a-real-gender"
    result = validate_resource(resource, patient_sd)
    assert not result.valid
    assert any(i.path == "gender" for i in result.issues)


def test_wrong_resource_type_is_reported(patient_sd):
    resource = {"resourceType": "Observation"}
    result = validate_resource(resource, patient_sd)
    assert not result.valid
    assert result.issues[0].path == "resourceType"


def test_deep_copy_independence(patient_sd):
    resource = generate_resource(patient_sd)
    resource2 = copy.deepcopy(resource)
    resource2["name"] = []
    result = validate_resource(resource2, patient_sd)
    assert not result.valid
    result_original = validate_resource(resource, patient_sd)
    assert result_original.valid


def test_cardinality_is_checked_per_instance_not_flattened():
    sd = StructureDefinition.from_dict(REPEATING_PARENT_SD)
    resource = {
        "resourceType": "Basic",
        "item": [{"code": "a"}, {"code": "b"}],
    }
    result = validate_resource(resource, sd)
    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]


def test_cardinality_violation_within_one_instance_is_still_caught():
    sd = StructureDefinition.from_dict(REPEATING_PARENT_SD)
    resource = {
        "resourceType": "Basic",
        "item": [{"code": "a"}, {"code": ["b", "c"]}],
    }
    result = validate_resource(resource, sd)
    assert not result.valid
    assert any(i.path == "item.code" for i in result.issues)
