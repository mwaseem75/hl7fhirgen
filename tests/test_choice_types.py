from hl7fhirgen.generator import generate_resource
from hl7fhirgen.structure_definition import StructureDefinition
from hl7fhirgen.validator import validate_resource

CHOICE_SD = {
    "resourceType": "StructureDefinition",
    "name": "ExampleObservation",
    "type": "Observation",
    "status": "draft",
    "snapshot": {
        "element": [
            {"id": "Observation", "path": "Observation", "min": 0, "max": "*"},
            {"id": "Observation.status", "path": "Observation.status", "min": 1, "max": "1",
             "type": [{"code": "code"}]},
            {"id": "Observation.value[x]", "path": "Observation.value[x]", "min": 1, "max": "1",
             "type": [{"code": "CodeableConcept"}], "mustSupport": True},
        ]
    },
}


def test_choice_type_generates_concrete_field_name():
    sd = StructureDefinition.from_dict(CHOICE_SD)
    resource = generate_resource(sd)
    assert "valueCodeableConcept" in resource
    assert "value[x]" not in resource
    assert isinstance(resource["valueCodeableConcept"], dict)


def test_choice_type_validates_against_concrete_field():
    sd = StructureDefinition.from_dict(CHOICE_SD)
    resource = generate_resource(sd)
    result = validate_resource(resource, sd)
    assert result.valid, [f"{i.path}: {i.message}" for i in result.issues]


def test_choice_type_missing_value_is_reported():
    sd = StructureDefinition.from_dict(CHOICE_SD)
    resource = {"resourceType": "Observation", "status": "final"}
    result = validate_resource(resource, sd)
    assert not result.valid
    assert any("value[x]" in i.path for i in result.issues)
