from hl7fhirgen.explainer import explain


def test_explain_contains_expected_sections(patient_sd):
    summary = explain(patient_sd)
    assert "# ExamplePatient (Patient)" in summary
    assert "## Required elements" in summary
    assert "`identifier`" in summary
    assert "`gender`" in summary
    assert "## Extensions" in summary
    assert "birthPlace" in summary
    assert "## Value set bindings" in summary
    assert "administrative-gender" in summary
    assert "## Fixed / pattern values" in summary
    assert "http://example.org/mrn" in summary
