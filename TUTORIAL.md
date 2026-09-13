# hl7fhirgen: a step-by-step tutorial

This walks through everything `hl7fhirgen` does, in order, using commands you can copy
and paste. Every example below was actually run to produce the output shown — if
something on your machine looks different, that's worth reporting (see
[CONTRIBUTING.md](CONTRIBUTING.md)).

## 1. Install it

```bash
pip install hl7fhirgen
```

No server, no terminology service, no license required. Check it worked:

```console
$ hl7fhirgen --version
hl7fhirgen, version 0.1.0
```

## 2. Write (or get) a profile

`hl7fhirgen` works against a FHIR **StructureDefinition** — the resource type that
describes a profile's rules (required fields, must-support fields, fixed values,
extensions, value-set bindings). You can point it at:
- A profile you download from an Implementation Guide (US Core, NPHIES, a national IG),
  Simplifier, or an IG-authoring tool.
- A profile you write yourself.

To follow along without downloading anything, save this as `my-profile.json`. It's a
small custom `Patient` profile: identifier and name are required, gender is required and
must be a real administrative-gender code, and the identifier's system is pinned.

```json
{
  "resourceType": "StructureDefinition",
  "id": "my-patient",
  "url": "http://example.org/fhir/StructureDefinition/my-patient",
  "name": "MyPatient",
  "status": "draft",
  "type": "Patient",
  "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
  "derivation": "constraint",
  "snapshot": {
    "element": [
      { "id": "Patient", "path": "Patient", "min": 0, "max": "*" },
      { "id": "Patient.identifier", "path": "Patient.identifier", "min": 1, "max": "1",
        "type": [{ "code": "Identifier" }], "mustSupport": true },
      { "id": "Patient.identifier.system", "path": "Patient.identifier.system",
        "min": 1, "max": "1", "type": [{ "code": "uri" }], "fixedUri": "http://example.org/mrn" },
      { "id": "Patient.name", "path": "Patient.name", "min": 1, "max": "*",
        "type": [{ "code": "HumanName" }], "mustSupport": true },
      { "id": "Patient.name.family", "path": "Patient.name.family",
        "min": 1, "max": "1", "type": [{ "code": "string" }] },
      { "id": "Patient.gender", "path": "Patient.gender", "min": 1, "max": "1",
        "type": [{ "code": "code" }],
        "binding": { "strength": "required", "valueSet": "http://hl7.org/fhir/ValueSet/administrative-gender" } }
    ]
  }
}
```

The important parts of any `ElementDefinition` entry: `path` (where it lives),
`min`/`max` (cardinality), `type` (the FHIR datatype), `mustSupport`, `fixedX`/`patternX`
(a value that must match exactly, or exactly-or-more, respectively), and `binding`
(which value set a coded field must come from).

## 3. Understand the profile before touching any data

```console
$ hl7fhirgen explain my-profile.json
# MyPatient (Patient)
`http://example.org/fhir/StructureDefinition/my-patient`

## Required elements
- `gender` [1..1] (code)
- `identifier` [1..1] (Identifier)
- `identifier.system` [1..1] (uri)
- `name` [1..*] (HumanName)
- `name.family` [1..1] (string)

## Must-support elements
_None._

## Extensions
_None._

## Value set bindings
- `gender` — **required**: http://hl7.org/fhir/ValueSet/administrative-gender

## Fixed / pattern values
- `identifier.system` — fixed to `http://example.org/mrn`
```

(`identifier` and `name` are must-support *and* required here, so they're only listed
once, under "Required elements" — `explain` doesn't repeat an element in both sections.)
This is the fastest way to answer "what does this profile actually need?" without
reading raw JSON — especially useful the first time you open an unfamiliar
Implementation Guide.

## 4. Generate a conformant example resource

```console
$ hl7fhirgen generate my-profile.json --out patient.json
Wrote patient.json

$ cat patient.json
{
  "resourceType": "Patient",
  "identifier": [
    {
      "use": "official",
      "system": "http://example.org/mrn",
      "value": "ID-66779163"
    }
  ],
  "name": [
    { "use": "official", "family": "Harrington", "given": ["Lindsay"] }
  ],
  "gender": "other"
}
```

Every required and must-support element is populated with plausible synthetic data —
Faker-generated names, a real administrative-gender code (because the binding is
`required`), and the fixed `identifier.system` value honored exactly. Add `--full` to
also populate every *optional* element, not just required/must-support ones.

## 5. Validate a resource against the profile

Try it on the resource you just generated — it should pass:

```console
$ hl7fhirgen validate patient.json --profile my-profile.json
Valid against MyPatient.
```

Now break it, to see what a real failure looks like:

```console
$ echo '{"resourceType": "Patient"}' > bad-patient.json
$ hl7fhirgen validate bad-patient.json --profile my-profile.json
[ERROR] identifier: required (min cardinality 1) but found 0
[ERROR] name: required (min cardinality 1) but found 0
[ERROR] gender: required (min cardinality 1) but found 0
```

`validate` checks cardinality, fixed/pattern values, required-strength bindings (for a
bundled set of well-known value sets), and basic primitive-type sanity. It's a
documented subset of full FHIR conformance checking, not a drop-in replacement for the
official HL7 FHIR Validator — see the README's "Scope" section for exactly what is and
isn't covered, and why (short version: things like terminology-server lookups and full
slicing-discriminator resolution are a much bigger lift, and `hl7fhirgen` would rather
tell you plainly what it checked than pretend to check everything).

## 6. The NPHIES pack: pre-submission claim checking

[NPHIES](https://nphies.sa) is Saudi Arabia's national FHIR-based claims and eligibility
exchange. The NPHIES pack adds claim-specific tooling on top of everything above. Clone
the repo to get the bundled example claim/claim-response files:

```bash
git clone https://github.com/mwaseem75/hl7fhirgen.git
cd hl7fhirgen
```

Check a claim response for recognized rejection patterns:

```console
$ hl7fhirgen nphies check-claim examples/nphies/claim-response-example.json \
    --profile examples/nphies/claim-response-example-profile.json
Valid against ExampleClaimResponse.

Recognized rejection codes (Community-sourced guidance seeded with illustrative examples, not an official NPHIES source. Verify against the current NPHIES Implementation Guide and your payer contract before acting on a real claim decision.):

- duplicate-claim: A claim for this patient/service/date appears to already be on file
    - The claim was already submitted and is still processing
    - A resubmission was sent without referencing the original claim
  Suggested fix: Check claim status before resubmitting; if correcting an earlier claim, reference it explicitly rather than submitting a fresh one.

- missing-preauth: A required pre-authorization was not obtained or referenced
    - The service/procedure requires prior authorization under the patient's plan
    - A pre-authorization exists but wasn't referenced on the claim
  Suggested fix: Confirm whether the billed service requires pre-auth for this plan; if a prior authorization exists, include its reference on resubmission, otherwise request one first.
```

Or look a specific code up directly:

```console
$ hl7fhirgen nphies explain-rejection duplicate-claim
$ hl7fhirgen nphies list-rejections
```

**Read this before relying on it for a real claim:** the rejection-code knowledge base
ships with a handful of illustrative example entries seeding its structure — it is a
community-maintained lookup table, not an official mirror of NPHIES's actual
terminology. `check-claim` validates against **whatever profile you supply**, so bring
your own copy of a real NPHIES profile from the NPHIES developer portal for actual
submissions. If you've hit a real rejection pattern in production, contributing it is
very welcome — see `CONTRIBUTING.md`.

## 7. Use it from Claude (MCP + Claude Code plugin)

```bash
pip install "hl7fhirgen[mcp]"
```

This installs the `hl7fhirgen-mcp` command, which exposes `generate_fhir_resource`,
`validate_fhir_resource`, `explain_profile`, and the three NPHIES tools over the [Model
Context Protocol](https://modelcontextprotocol.io) — any MCP client (Claude Desktop,
Claude Code, etc.) can call them directly instead of shelling out to the CLI.

For Claude Code specifically, install it as a plugin:

```
/plugin marketplace add mwaseem75/hl7fhirgen
/plugin install hl7fhirgen@hl7fhirgen-marketplace
```

This bundles the MCP server with a skill that teaches Claude when to reach for
`hl7fhirgen` and flags real gotchas found while building it (FHIR's array-vs-scalar JSON
shape rules, choice-type resolution, per-instance cardinality checking).

## 8. Add it to CI with the GitHub Action

Gate a pull request on every test resource still validating against your profile:

```yaml
- uses: mwaseem75/hl7fhirgen/action@master
  with:
    command: validate
    profile-path: profiles/my-profile.json
    resource-path: test-data/patient.json
```

`command` can also be `generate` or `explain`. See `action/action.yml` for every input.

## 9. Try the web playground

If you'd rather click than type, run the whole thing in a browser:

```bash
git clone https://github.com/mwaseem75/hl7fhirgen.git
cd hl7fhirgen
docker compose up --build
```

Open http://localhost:8000 — generate, validate, explain, and run the NPHIES pack's
`check-claim`, with the same bundled examples this tutorial uses pre-loadable from a
dropdown. You can also deploy your own copy to [Render](https://dashboard.render.com)
via **New +** → **Blueprint** (it picks up `render.yaml` automatically).

## Where to go next

- Full command reference and what's checked/not checked: [README.md](README.md)
- Project layout, testing conventions, how to report a bug: [CONTRIBUTING.md](CONTRIBUTING.md)
- Release history: [CHANGELOG.md](CHANGELOG.md)
- Questions, real-world profiles you'd like better support for, or a real NPHIES
  rejection pattern to contribute: open an issue at
  https://github.com/mwaseem75/hl7fhirgen/issues
