# Contributing to hl7FHIRGen

## Setup

```bash
git clone https://github.com/mwaseem75/hl7fhirgen.git
cd hl7fhirgen
pip install -e ".[dev]"
pytest
```

## Project layout

```
src/hl7fhirgen/
  structure_definition.py   parses StructureDefinition JSON into ElementDefinition/StructureDefinition
  generator.py               builds a synthetic conformant resource from a StructureDefinition
  validator.py                checks a resource against a StructureDefinition
  explainer.py                renders a StructureDefinition as plain-English markdown
  fhir_datatypes.py          Faker-based synthetic value generators per FHIR datatype
  cli.py                      click CLI wiring the above together
examples/                    hand-authored demo profile used in README and tests
tests/                       pytest suite (one test file per module, plus test_cli.py)
```

## Making a change

1. Add or update tests in `tests/` first — every module has a corresponding test file.
2. Run `pytest` before opening a PR; CI runs the same suite across Python 3.10-3.12.
3. Keep the "Scope" section of `README.md` in sync if you add or remove a documented
   limitation (e.g. widening `ALWAYS_ARRAY_FIELDS` in `generator.py`, adding a value set
   to `fhir_datatypes.KNOWN_VALUE_SETS`).
4. Prefer extending an existing module over adding a new one — the package is
   deliberately small and flat.

## Reporting a profile that generates or validates incorrectly

Please include:
- The StructureDefinition JSON (or a minimal excerpt reproducing the issue).
- The command you ran and its output.
- What you expected instead.

If the StructureDefinition uses a construct called out in README's "Scope" section
(differential-only profiles, slicing beyond extensions, non-inlined extension value
types, terminology outside `KNOWN_VALUE_SETS`), that's a known, documented gap rather
than a bug — but a PR extending coverage for it is very welcome.
