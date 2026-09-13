---
name: hl7fhirgen
description: Use when generating, validating, or explaining FHIR resources against a StructureDefinition profile, or checking a claim/eligibility resource for NPHIES-style rejection patterns. Covers profile-aware synthetic resource generation, cardinality/fixed/pattern/binding validation against any profile (national IG, US Core, custom, or your own), plain-English profile summaries, and a pre-submission claim-rejection knowledge base. Triggers on requests like "generate a FHIR resource for this profile", "validate this resource against a StructureDefinition", "explain this FHIR profile", "what does this extension require", "check this claim before submitting to NPHIES", "explain this rejection code".
---

# hl7fhirgen

Generates, validates, and explains FHIR resources against any `StructureDefinition`
profile — no vendor lock-in, no terminology server required. Includes an NPHIES pack
for pre-submission claim checking and rejection-code lookups.

## How to reach it

If the `hl7fhirgen` MCP server is connected (bundled with this plugin), prefer its
tools — they take profile/resource JSON directly (as strings), no shelling out:
`generate_fhir_resource`, `validate_fhir_resource`, `explain_profile`,
`nphies_check_claim`, `nphies_explain_rejection`, `nphies_list_rejection_codes`.

Otherwise, use the CLI (`pip install hl7fhirgen`):
```bash
hl7fhirgen generate my-profile.json --full
hl7fhirgen validate resource.json --profile my-profile.json
hl7fhirgen explain my-profile.json
hl7fhirgen nphies check-claim resource.json --profile my-profile.json
hl7fhirgen nphies explain-rejection duplicate-claim
```

Or import the library directly in Python: `hl7fhirgen.generator.generate_resource`,
`hl7fhirgen.validator.validate_resource`, `hl7fhirgen.explainer.explain`,
`hl7fhirgen.packs.nphies.check_claim`.

## Things worth knowing before using it

- **This is a documented subset of full FHIR conformance checking**, not a
  replacement for the official HL7 FHIR Validator — no terminology server, no
  cross-element invariants, no full slicing-discriminator resolution. It checks
  cardinality, fixed/pattern values, required-strength bindings for a small bundled
  set of well-known value sets, and basic primitive-type sanity. See the project's
  README "Scope" section for the exact list — don't assume a clean validation result
  means the resource would pass the official validator too.
- **FHIR's JSON shape (array vs. scalar) follows the *base* resource's cardinality,
  not a profile's narrowed max.** `Patient.identifier` is still `"identifier": [...]`
  even in a profile that pins it to `0..1`. The generator hardcodes this for common
  base-repeating elements (`identifier`, `name`, `telecom`, `address`, `given`,
  `extension`, `coding`, ...) — an element outside that list that's actually
  repeating in the base spec but not recognized here can generate as a scalar
  incorrectly. This bit the project during its own development.
- **Choice-type elements (`value[x]`, `diagnosis[x]`, etc.) are resolved to their
  concrete JSON key** (e.g. `valueString`, `diagnosisCodeableConcept`) based on the
  profile's declared type — both when generating and when validating.
- **Cardinality is checked per parent instance, not flattened** — e.g. a repeating
  `Claim.item` with a `0..1 Claim.item.quantity` is checked per item, not by pooling
  every item's quantities into one count across the whole resource. An earlier
  version of this tool got this wrong; it's now covered by a regression test.
- **The NPHIES pack's rejection-code knowledge base is community-sourced and
  illustrative**, not an official mirror of NPHIES's terminology — hl7fhirgen has no
  live feed of NPHIES's actual CodeSystem. Every result includes a disclaimer;
  surface it to the user rather than presenting a rejection explanation as
  authoritative. `check-claim`/`nphies_check_claim` validates against whatever
  profile you supply — point it at your own copy of a real NPHIES profile for
  actual submissions.
- **Extension value-type detection only works when a profile inlines `value[x]`
  for the slice** (or you pass the type explicitly some other way) — since this
  tool doesn't fetch external extension `StructureDefinition`s over the network, an
  extension slice with no inline `value[x]` generates a generic `valueString`
  placeholder instead of the real value type.
