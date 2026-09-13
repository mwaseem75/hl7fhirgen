from hl7fhirgen.generator import generate_resource


def test_generates_required_and_must_support_fields(patient_sd):
    resource = generate_resource(patient_sd)

    assert resource["resourceType"] == "Patient"

    assert resource["identifier"][0]["system"] == "http://example.org/mrn"
    assert isinstance(resource["identifier"][0]["value"], str)

    assert isinstance(resource["name"][0]["family"], str)
    assert isinstance(resource["name"][0]["given"], list)

    assert resource["gender"] in {"male", "female", "other", "unknown"}

    # must-support, not required -> still populated by default
    assert "birthDate" in resource


def test_extension_generated_with_detected_value_type(patient_sd):
    resource = generate_resource(patient_sd, include_optional=True)
    ext = next(e for e in resource["extension"] if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-birthPlace")
    assert "valueAddress" in ext
    assert isinstance(ext["valueAddress"], dict)


def test_optional_only_included_with_full_flag(patient_sd):
    minimal = generate_resource(patient_sd, include_optional=False)
    full = generate_resource(patient_sd, include_optional=True)
    assert "extension" not in minimal
    assert "extension" in full
