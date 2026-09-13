"""Synthetic-value generators for FHIR primitive and common complex datatypes.

Scope: covers the datatypes that show up in the overwhelming majority of
real-world profiles (demographics, identifiers, contact info, references,
codes). Anything not listed here falls back to a generic placeholder string
in `generator.py` rather than raising — see README "Scope".
"""
from __future__ import annotations

import random
import uuid

from faker import Faker

_fake = Faker()

# A handful of well-known, stable value sets worth honoring directly instead
# of emitting an arbitrary made-up code (keeps generated data plausible for
# the bindings people actually check against).
KNOWN_VALUE_SETS: dict[str, list[str]] = {
    "http://hl7.org/fhir/ValueSet/administrative-gender": ["male", "female", "other", "unknown"],
    "http://hl7.org/fhir/ValueSet/identifier-use": ["usual", "official", "temp", "secondary", "old"],
    "http://hl7.org/fhir/ValueSet/name-use": ["usual", "official", "temp", "nickname", "old"],
    "http://hl7.org/fhir/ValueSet/contact-point-system": ["phone", "fax", "email", "pager", "url", "sms", "other"],
    "http://hl7.org/fhir/ValueSet/contact-point-use": ["home", "work", "temp", "old", "mobile"],
}


def fake_primitive(type_code: str) -> object:
    generators = {
        "boolean": lambda: random.choice([True, False]),
        "integer": lambda: random.randint(0, 100),
        "positiveInt": lambda: random.randint(1, 100),
        "unsignedInt": lambda: random.randint(0, 100),
        "decimal": lambda: round(random.uniform(0, 100), 2),
        "date": lambda: _fake.date(pattern="%Y-%m-%d"),
        "dateTime": lambda: _fake.date_time().isoformat() + "Z",
        "instant": lambda: _fake.date_time().isoformat() + "Z",
        "time": lambda: _fake.time(),
        "string": lambda: _fake.sentence(nb_words=4).rstrip("."),
        "markdown": lambda: _fake.sentence(nb_words=8).rstrip("."),
        "code": lambda: "example-code",
        "id": lambda: str(uuid.uuid4()),
        "uri": lambda: f"http://example.org/{_fake.word()}",
        "url": lambda: f"http://example.org/{_fake.word()}",
        "canonical": lambda: f"http://example.org/{_fake.word()}",
        "base64Binary": lambda: "ZXhhbXBsZQ==",
        "oid": lambda: "urn:oid:1.2.3.4.5",
        "uuid": lambda: f"urn:uuid:{uuid.uuid4()}",
    }
    gen = generators.get(type_code)
    return gen() if gen else f"example-{type_code}"


def fake_code_for_binding(binding: dict | None, fallback_type_code: str = "code") -> object:
    if binding:
        value_set = binding.get("valueSet", "").split("|")[0]  # strip version pin
        options = KNOWN_VALUE_SETS.get(value_set)
        if options:
            return random.choice(options)
    return fake_primitive(fallback_type_code)


def fake_coding() -> dict:
    return {
        "system": "http://example.org/CodeSystem/example",
        "code": "example",
        "display": _fake.word().title(),
    }


def fake_codeable_concept() -> dict:
    return {"coding": [fake_coding()], "text": _fake.word().title()}


def fake_identifier() -> dict:
    return {
        "use": "official",
        "system": "http://example.org/identifiers",
        "value": _fake.bothify(text="ID-########"),
    }


def fake_human_name() -> dict:
    return {
        "use": "official",
        "family": _fake.last_name(),
        "given": [_fake.first_name()],
    }


def fake_address() -> dict:
    return {
        "use": "home",
        "line": [_fake.street_address()],
        "city": _fake.city(),
        "postalCode": _fake.postcode(),
        "country": _fake.country_code(),
    }


def fake_contact_point() -> dict:
    return {"system": "phone", "value": _fake.phone_number(), "use": "mobile"}


def fake_period() -> dict:
    start = _fake.date_time()
    return {"start": start.isoformat() + "Z"}


def fake_quantity() -> dict:
    return {"value": round(random.uniform(1, 200), 1), "unit": "unit", "system": "http://unitsofmeasure.org"}


def fake_reference(target_type: str = "Resource") -> dict:
    return {"reference": f"{target_type}/{uuid.uuid4()}"}


COMPLEX_TYPE_FAKERS = {
    "CodeableConcept": fake_codeable_concept,
    "Coding": fake_coding,
    "Identifier": fake_identifier,
    "HumanName": fake_human_name,
    "Address": fake_address,
    "ContactPoint": fake_contact_point,
    "Period": fake_period,
    "Quantity": fake_quantity,
}

PRIMITIVE_TYPES = {
    "boolean", "integer", "positiveInt", "unsignedInt", "decimal", "date", "dateTime",
    "instant", "time", "string", "markdown", "code", "id", "uri", "url", "canonical",
    "base64Binary", "oid", "uuid",
}

# When a profile drills down into a normally-composite element's sub-fields
# (e.g. constrains HumanName.family directly instead of leaving HumanName
# alone), we lose the complex-type-level faker's realism. These field-name
# hints patch the common cases back up — anything not listed here still gets
# a generic (if less realistic) value for its declared primitive type.
FIELD_NAME_FAKERS = {
    "family": lambda: _fake.last_name(),
    "given": lambda: _fake.first_name(),
    "prefix": lambda: random.choice(["Mr.", "Mrs.", "Dr.", "Ms."]),
    "suffix": lambda: random.choice(["Jr.", "Sr.", "II", "III"]),
    "city": lambda: _fake.city(),
    "postalCode": lambda: _fake.postcode(),
    "country": lambda: _fake.country_code(),
    "line": lambda: _fake.street_address(),
    "display": lambda: _fake.word().title(),
    "value": lambda: _fake.bothify(text="ID-########"),
}


def fake_value_for_type(
    type_code: str,
    binding: dict | None = None,
    field_name: str | None = None,
    target_type: str | None = None,
) -> object:
    if type_code in PRIMITIVE_TYPES:
        if type_code == "code" and binding:
            return fake_code_for_binding(binding, fallback_type_code="code")
        hint = FIELD_NAME_FAKERS.get(field_name) if field_name else None
        if hint and type_code == "string":
            return hint()
        return fake_primitive(type_code)
    if type_code == "Reference":
        return fake_reference(target_type or "Resource")
    faker_fn = COMPLEX_TYPE_FAKERS.get(type_code)
    if faker_fn:
        return faker_fn()
    return f"example-{type_code}"
