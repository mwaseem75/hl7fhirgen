from hl7fhirgen.structure_definition import StructureDefinitionError, StructureDefinition


def test_loads_type_and_metadata(patient_sd):
    assert patient_sd.type == "Patient"
    assert patient_sd.name == "ExamplePatient"
    assert patient_sd.used_fallback_differential is False


def test_required_elements(patient_sd):
    required_paths = {patient_sd.relative_path(el) for el in patient_sd.required_elements()}
    assert required_paths == {
        "identifier", "identifier.system", "identifier.value",
        "name", "name.family", "name.given", "gender",
    }


def test_must_support_elements(patient_sd):
    ms_paths = {patient_sd.relative_path(el) for el in patient_sd.must_support_elements()}
    assert "birthDate" in ms_paths
    assert "identifier" in ms_paths


def test_extension_slices(patient_sd):
    slices = patient_sd.extension_slices()
    assert len(slices) == 1
    assert slices[0].slice_name == "birthPlace"


def test_bound_elements(patient_sd):
    bound = patient_sd.bound_elements()
    assert any(patient_sd.relative_path(el) == "gender" for el in bound)


def test_immediate_children_top_level(patient_sd):
    top_level = patient_sd.immediate_children("")
    top_paths = {patient_sd.relative_path(el) for el in top_level}
    assert top_paths == {"identifier", "name", "gender", "birthDate", "extension"}


def test_rejects_non_structure_definition():
    import pytest
    with pytest.raises(StructureDefinitionError):
        StructureDefinition.from_dict({"resourceType": "Patient"})
