# Contributing to hl7FHIRGen

## Setup

```bash
git clone https://github.com/mwaseem75/hl7fhirgen.git
cd hl7fhirgen
pip install -e ".[dev,mcp]"
pytest
```

## Project layout

```
src/hl7fhirgen/
  structure_definition.py   parses StructureDefinition JSON into ElementDefinition/StructureDefinition
                             (also home to choice-type helpers: CHOICE_SUFFIX, choice_field_name)
  generator.py               builds a synthetic conformant resource from a StructureDefinition
  validator.py                checks a resource against a StructureDefinition, per parent instance
  explainer.py                renders a StructureDefinition as plain-English markdown
  fhir_datatypes.py          Faker-based synthetic value generators per FHIR datatype
  cli.py                      click CLI wiring the above together
  mcp_server.py               MCP server exposing the same functions as tools (stdio transport)
  packs/nphies/               NPHIES pack: rejection_codes.py (knowledge base), check_claim.py
examples/                    hand-authored demo profiles used in README and tests, incl. examples/nphies/
action/                      GitHub Action wrapping the CLI
tests/                       pytest suite (one test file per module, plus test_cli.py, test_mcp_server.py)
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

## Contributing a real NPHIES rejection pattern

`src/hl7fhirgen/packs/nphies/rejection_codes.py` ships with illustrative example
entries only — see its module docstring and the README's "NPHIES pack" section for
why. If you've encountered a real rejection pattern in production, a PR adding it is
very welcome. Please:
- Use a descriptive slug as the key (not a raw NPHIES code value, to avoid the table
  being mistaken for an authoritative enumeration of NPHIES's terminology).
- Describe the general pattern and likely causes, not any patient- or
  claim-identifying detail.
- Keep the tone the same as the existing entries: practical, not definitive.
