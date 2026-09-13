"""Generates a synthetic FHIR resource that conforms to a StructureDefinition.

Populates every required element (min >= 1) and every must-support element;
optional elements are included too when `include_optional=True`. Fixed and
pattern values are honored verbatim. See README "Scope" for what slicing and
extension handling do and don't cover in v1.
"""
from __future__ import annotations

from hl7fhirgen import fhir_datatypes
from hl7fhirgen.structure_definition import ElementDefinition, StructureDefinition

# FHIR's JSON *shape* (array vs. scalar) is fixed by the base resource's own
# cardinality, not by how far a profile narrows it — e.g. Patient.identifier
# is still `"identifier": [...]` even in a profile that pins it to 0..1. We
# don't load the base StructureDefinition in v1, so this is a hardcoded list
# of the common elements that are always arrays in the base spec. Anything
# else relies on the profile's own (possibly narrowed) max — a documented gap
# for elements not in this list. See README "Scope".
ALWAYS_ARRAY_FIELDS = {
    "identifier", "name", "telecom", "address", "given", "prefix", "suffix", "line",
    "extension", "modifierExtension", "coding", "contact", "communication", "link",
    "generalPractitioner", "photo", "note",
}


def generate_resource(sd: StructureDefinition, include_optional: bool = False) -> dict:
    resource: dict = {"resourceType": sd.type}
    _populate_children(resource, sd, prefix="", include_optional=include_optional)
    return resource


def _should_include(el: ElementDefinition, include_optional: bool) -> bool:
    return el.is_required or el.must_support or include_optional


def _populate_children(container: dict, sd: StructureDefinition, prefix: str, include_optional: bool) -> None:
    children = sd.immediate_children(prefix)
    by_path: dict[str, list[ElementDefinition]] = {}
    for el in children:
        by_path.setdefault(sd.relative_path(el), []).append(el)

    for rel_path, els in by_path.items():
        field_name = rel_path.split(".")[-1]

        if field_name == "extension":
            extensions = _build_extensions(els, sd, include_optional)
            if extensions:
                container["extension"] = extensions
            continue

        primary = els[0]
        if not any(_should_include(e, include_optional) for e in els):
            continue

        is_list = (
            primary.max_is_unbounded
            or (primary.max_int or 1) > 1
            or field_name in ALWAYS_ARRAY_FIELDS
        )
        count = max(primary.min, 1)
        values = [_build_value(primary, sd, rel_path, include_optional) for _ in range(count)]
        values = [v for v in values if v is not None]
        if not values:
            continue
        container[field_name] = values if is_list else values[0]


def _build_value(el: ElementDefinition, sd: StructureDefinition, rel_path: str, include_optional: bool):
    if el.fixed:
        _, value = el.fixed
        return value
    if el.pattern:
        _, value = el.pattern
        return value

    type_code = el.type_codes[0] if el.type_codes else "string"

    child_defs = sd.immediate_children(rel_path)
    if child_defs:
        base: dict = {}
        faker_fn = fhir_datatypes.COMPLEX_TYPE_FAKERS.get(type_code)
        if faker_fn:
            base = faker_fn()
        _populate_children(base, sd, rel_path, include_optional)
        return base

    field_name = rel_path.split(".")[-1]
    return fhir_datatypes.fake_value_for_type(type_code, el.binding, field_name=field_name)


def _build_extensions(ext_els: list[ElementDefinition], sd: StructureDefinition, include_optional: bool) -> list[dict]:
    result = []
    for el in ext_els:
        if not _should_include(el, include_optional):
            continue

        url = None
        if el.types and el.types[0].get("profile"):
            url = el.types[0]["profile"][0]
        elif el.slice_name:
            url = el.slice_name
        if not url:
            continue

        rel_path = sd.relative_path(el)
        value_children = [
            c for c in sd.immediate_children(rel_path)
            if sd.relative_path(c).split(".")[-1].startswith("value")
        ]
        if value_children:
            vchild = value_children[0]
            vtype = vchild.type_codes[0] if vchild.type_codes else "string"
            value_field = "value" + vtype[0].upper() + vtype[1:]
            value = fhir_datatypes.fake_value_for_type(vtype, vchild.binding)
        else:
            value_field, value = "valueString", "example-extension-value"

        result.append({"url": url, value_field: value})
    return result
