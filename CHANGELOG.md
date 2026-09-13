# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-09-13

### Added
- `structure_definition.py` — parses a FHIR `StructureDefinition` (snapshot preferred,
  differential fallback) into `ElementDefinition`/`StructureDefinition` dataclasses.
- `generator.py` — generates a synthetic resource conforming to a profile: required and
  must-support elements populated, fixed/pattern values honored, known value-set
  bindings respected, correct array-vs-scalar JSON shape for common base-repeating
  elements (`identifier`, `name`, `telecom`, `address`, `given`, `extension`, ...).
- `validator.py` — checks cardinality, fixed/pattern values, required-strength bindings
  (against a bundled set of well-known value sets), and basic primitive-type sanity.
- `explainer.py` — renders a profile as a plain-English markdown summary.
- `fhir_datatypes.py` — Faker-based synthetic value generators per FHIR datatype, with
  field-name hints for realism when a profile drills into a complex type's sub-fields.
- `cli.py` — `hl7fhirgen generate|validate|explain`, via click.
- `examples/patient-example-profile.json` — hand-authored demo profile used in the
  README and test suite.
- pytest suite (20 tests) and GitHub Actions CI across Python 3.10-3.12.

[0.1.0]: https://github.com/mwaseem75/hl7fhirgen/releases/tag/v0.1.0
