# hl7FHIRGen

[![Tests](https://github.com/mwaseem75/hl7fhirgen/actions/workflows/test.yml/badge.svg)](https://github.com/mwaseem75/hl7fhirgen/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Generate, validate, and explain FHIR resources against any StructureDefinition
profile — for any FHIR IG, with no vendor lock-in.

```bash
pip install hl7fhirgen
hl7fhirgen generate my-profile.json
```

That's it — no server, no terminology service, no license required. Point it at
any StructureDefinition: a national IG like NPHIES, US Core, a custom hospital
profile, or one you're authoring yourself.

## Why

Working with FHIR profiles is one of the most painful parts of implementing
FHIR in practice: reading a raw `StructureDefinition` differential to figure
out what's actually required, generating a conformant test resource by hand,
or checking a resource against a profile all normally mean either wading
through JSON yourself or reaching for a heavyweight Java validator.
`hl7fhirgen` is a small, free, scriptable tool that closes that gap for the
everyday cases: generate a conformant example, validate a resource against a
profile, and get a plain-English summary of what a profile actually requires.

## Demo

```console
$ hl7fhirgen generate examples/patient-example-profile.json --full
{
  "resourceType": "Patient",
  "identifier": [
    {
      "use": "official",
      "system": "http://example.org/mrn",
      "value": "ID-49247090"
    }
  ],
  "name": [
    { "use": "official", "family": "Haynes", "given": ["Kelly"] }
  ],
  "gender": "unknown",
  "birthDate": "1971-12-03",
  "extension": [
    {
      "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
      "valueAddress": { "use": "home", "line": ["458 Charles Meadow Apt. 615"], "city": "West Sarahburgh", "postalCode": "14285", "country": "MA" }
    }
  ]
}

$ hl7fhirgen validate patient.json --profile examples/patient-example-profile.json
Valid against ExamplePatient.

$ hl7fhirgen explain examples/patient-example-profile.json
# ExamplePatient (Patient)
...
## Required elements
- `gender` [1..1] (code) — Administrative gender
- `identifier` [1..1] (Identifier) — Medical record number
- `identifier.system` [1..1] (uri)
- `identifier.value` [1..1] (string)
- `name` [1..*] (HumanName) — Patient's name
- `name.family` [1..1] (string)
- `name.given` [1..*] (string)
...
```

## Features

- **Generate** — feed it a `StructureDefinition` JSON file (from Simplifier, an
  IG build, or your own IDE) and get back a synthetic resource that satisfies
  every required and must-support element, honoring fixed/pattern values and
  standard value-set bindings. `--full` also fills in optional elements.
- **Validate** — check a resource against a profile: cardinality, fixed/pattern
  values, required-strength bindings (for the value sets it knows), and basic
  primitive-type sanity. See [Scope](#scope) — this is a documented subset of
  full FHIR conformance checking, not a replacement for the official validator.
- **Explain** — turn any `StructureDefinition` into a plain-English markdown
  summary: required elements, must-support elements, extensions, value-set
  bindings, and fixed/pattern constraints. Useful the moment you open an
  unfamiliar IG.

## CLI

```bash
hl7fhirgen generate my-profile.json --full --out patient.json
hl7fhirgen validate patient.json --profile my-profile.json
hl7fhirgen explain my-profile.json --out summary.md
```

## Scope

Full FHIR conformance validation — terminology services, slicing
discriminators, cross-element invariants (`.constraint`), full base-resource
merging of differentials — is a large, multi-year effort the official
[HL7 FHIR Validator](https://confluence.hl7.org/display/FHIR/Using+the+FHIR+Validator)
already does well. `hl7fhirgen` doesn't try to replace it. What it does today:

- Reads `snapshot.element` (the normal case for any profile from an IG,
  Simplifier, or an authoring tool); falls back to `differential.element` with
  a caveat if no snapshot is present — inherited base elements not listed in
  the differential won't be generated or checked.
- Honors `min`/`max` cardinality, `fixed[x]`/`pattern[x]`, and `required`/
  `extensible`-strength bindings for the small set of well-known value sets it
  ships with (administrative-gender, name-use, identifier-use, contact-point
  system/use). Other bindings are recognized but not checked against an actual
  terminology server.
- Detects array-vs-scalar JSON shape correctly for the common FHIR elements
  that are always arrays in the base spec (`identifier`, `name`, `telecom`,
  `address`, `given`, `extension`, `coding`, etc.) even when a profile narrows
  them to `0..1` — FHIR's JSON shape follows the *base* resource, not the
  profile's narrowed cardinality. Elements outside that list rely on the
  profile's own max and can be wrong if narrowed from a repeating base field
  we don't recognize.
- Extension value-type detection works when a profile inlines `value[x]` for
  the slice (as the bundled example does) or you otherwise know the type;
  since v1 doesn't fetch external extension `StructureDefinition`s over the
  network, an extension slice with no inline `value[x]` gets a generic
  `valueString` placeholder.
- Slicing support beyond extensions is best-effort: a repeating element with
  multiple named slices generates using the first slice's constraints only.

None of this is hidden — `hl7fhirgen validate` reports exactly what it
checked, and unsupported constructs are meant to fail loudly rather than
silently pass.

## Project layout

```
src/hl7fhirgen/   core package (structure_definition, generator, validator, explainer, fhir_datatypes, cli)
examples/         a hand-authored demo profile used in the README and tests
tests/            pytest suite
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

See `CONTRIBUTING.md` for the project layout, testing conventions, and how to report a
profile that generates or validates incorrectly. `CHANGELOG.md` tracks released versions.
Every public function and class has a docstring — `help(hl7fhirgen.generator)` (or your
editor's hover/go-to-definition) works from a plain `pip install`.

## Roadmap

- NPHIES profile pack: synthetic eligibility/claim/pre-auth resources, a
  pre-submission `check-claim` command, and a community-sourced rejection-code
  explainer — built from NPHIES's publicly published FHIR IG.
- Web playground (paste a resource + profile, get instant feedback in the
  browser).
- MCP server + Claude Code plugin, so any MCP-capable AI client can call
  generate/validate/explain directly.
- GitHub Action for CI validation of FHIR resources against an IG.
- Optional `--strict` mode that shells out to the official validator jar for
  authoritative validation when installed.

## License

MIT — see `LICENSE`.
