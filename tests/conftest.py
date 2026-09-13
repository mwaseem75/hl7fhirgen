from pathlib import Path

import pytest

from hl7fhirgen.structure_definition import load_structure_definition

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
NPHIES_EXAMPLES_DIR = EXAMPLES_DIR / "nphies"


@pytest.fixture
def patient_sd():
    return load_structure_definition(str(EXAMPLES_DIR / "patient-example-profile.json"))


@pytest.fixture
def patient_sd_json():
    return (EXAMPLES_DIR / "patient-example-profile.json").read_text(encoding="utf-8")


@pytest.fixture
def nphies_examples_dir():
    return NPHIES_EXAMPLES_DIR
