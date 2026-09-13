from pathlib import Path

import pytest

from hl7fhirgen.structure_definition import load_structure_definition

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def patient_sd():
    return load_structure_definition(str(EXAMPLES_DIR / "patient-example-profile.json"))
