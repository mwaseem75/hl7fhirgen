# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-09-14

First release, published to [PyPI](https://pypi.org/project/hl7fhirgen/0.1.0/).

### Added
- `structure_definition.py` — parses a FHIR `StructureDefinition` (snapshot preferred,
  differential fallback) into `ElementDefinition`/`StructureDefinition` dataclasses.
  Also home to `CHOICE_SUFFIX`/`choice_field_name` for choice-type resolution.
- `generator.py` — generates a synthetic resource conforming to a profile: required and
  must-support elements populated, fixed/pattern values honored, known value-set
  bindings respected, correct array-vs-scalar JSON shape for common base-repeating
  elements (`identifier`, `name`, `telecom`, `address`, `given`, `extension`, ...),
  generic support for choice-type elements (`value[x]`, `diagnosis[x]`, etc.) resolved
  to their concrete JSON key, and `targetProfile`-aware References (e.g.
  `"Patient/<uuid>"` instead of a generic `"Resource/<uuid>"`).
- `validator.py` — checks cardinality, fixed/pattern values, required-strength bindings
  (against a bundled set of well-known value sets), and basic primitive-type sanity,
  evaluated per parent instance (not flattened across a repeating element's instances)
  and choice-type aware.
- `explainer.py` — renders a profile as a plain-English markdown summary.
- `fhir_datatypes.py` — Faker-based synthetic value generators per FHIR datatype, with
  field-name hints for realism when a profile drills into a complex type's sub-fields.
- `cli.py` — `hl7fhirgen generate|validate|explain` plus `hl7fhirgen
  nphies check-claim|explain-rejection|list-rejections`, via click.
- `packs/nphies/` — NPHIES pack: `check_claim()` (validate + rejection-code
  cross-referencing) and a community-editable rejection-pattern knowledge base
  (`rejection_codes.py`, illustrative examples only — see its docstring and the
  README's "NPHIES pack" section).
- `mcp_server.py` — MCP server (stdio) exposing `generate_fhir_resource`,
  `validate_fhir_resource`, `explain_profile`, and the NPHIES pack's tools. Claude Code
  plugin manifest (`.claude-plugin/`), `.mcp.json`, `manifest.json` for MCPB packaging,
  and `SKILL.md`.
- `action/action.yml` — composite GitHub Action wrapping
  `generate`/`validate`/`explain` for CI.
- `webapp/` — FastAPI web playground (generate/validate/explain + the NPHIES pack's
  check-claim and rejection lookup, all in the browser) with a vanilla-JS static
  frontend, `Dockerfile`, `docker-compose.yml`, and `render.yaml` for one-click deploy.
- `examples/patient-example-profile.json` and `examples/nphies/` — hand-authored demo
  profiles/resources used in the README and test suite.
- pytest suite (47 tests) and GitHub Actions CI across Python 3.10-3.12.

[0.1.0]: https://github.com/mwaseem75/hl7fhirgen/releases/tag/v0.1.0
