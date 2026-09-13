import copy

from hl7fhirgen.generator import generate_resource
from hl7fhirgen.validator import validate_resource


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
