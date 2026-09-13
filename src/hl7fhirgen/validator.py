"""Validates a FHIR resource (as a dict) against a StructureDefinition.

Checks cardinality, fixed/pattern values, required-strength bindings against
the small set of value sets `fhir_datatypes.KNOWN_VALUE_SETS` ships, and basic
primitive-type sanity. This is a documented subset of full FHIR conformance
checking (no terminology server, no cross-element invariants/slicing
discriminators) — see README "Scope". Use `--strict` (shells out to the
official HL7 validator, when installed) for authoritative validation.

Cardinality and constraints are checked per parent instance, not flattened
across the whole resource — e.g. for a repeating `Claim.item` with a `0..1`
`Claim.item.quantity`, each item is checked to have at most one `quantity` of
its own, rather than pooling every item's quantities into one count.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from hl7fhirgen import fhir_datatypes
from hl7fhirgen.structure_definition import CHOICE_SUFFIX, ElementDefinition, StructureDefinition, choice_field_name

_DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
_DATETIME_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2}(T[\d:.]+(Z|[+-]\d{2}:\d{2})?)?)?)?$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}(:\d{2}(\.\d+)?)?$")

_PRIMITIVE_CHECKS = {
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "positiveInt": lambda v: isinstance(v, int) and not isinstance(v, bool) and v > 0,
    "unsignedInt": lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0,
    "decimal": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "date": lambda v: isinstance(v, str) and bool(_DATE_RE.match(v)),
    "dateTime": lambda v: isinstance(v, str) and bool(_DATETIME_RE.match(v)),
    "instant": lambda v: isinstance(v, str) and bool(_DATETIME_RE.match(v)),
    "time": lambda v: isinstance(v, str) and bool(_TIME_RE.match(v)),
}


@dataclass
class ValidationIssue:
    """One validation finding.

    Attributes:
        severity: "error" (makes the resource invalid) or "warning".
        path: The relative element path the issue applies to, e.g. "name.family".
        message: Human-readable description of the problem.
    """

    severity: str  # "error" | "warning"
    path: str
    message: str


@dataclass
class ValidationResult:
    """The outcome of `validate_resource`: a list of issues plus a `valid` summary."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """True if there are no issues at "error" severity."""
        return not any(i.severity == "error" for i in self.issues)


def _pattern_matches(actual, pattern) -> bool:
    if isinstance(pattern, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and _pattern_matches(actual[k], v) for k, v in pattern.items())
    return actual == pattern


def _field_values(container: dict, raw_field_name: str, type_codes: list[str]) -> list:
    """Read `raw_field_name` off `container`, resolving a choice-type suffix (e.g.
    "value[x]") against every concrete key it could have been serialized as, and
    normalizing a scalar-or-list JSON value into a flat list of instances.
    """
    if raw_field_name.endswith(CHOICE_SUFFIX):
        base = raw_field_name[: -len(CHOICE_SUFFIX)]
        candidates = [choice_field_name(base, tc) for tc in type_codes] or [base]
    else:
        candidates = [raw_field_name]

    values = []
    for candidate in candidates:
        if candidate in container:
            v = container[candidate]
            values.extend(v if isinstance(v, list) else [v])
    return values


def validate_resource(resource: dict, sd: StructureDefinition) -> ValidationResult:
    """Check `resource` against `sd` (see module docstring for exactly what's checked).

    Args:
        resource: The FHIR resource to validate, as a plain dict.
        sd: The profile to validate against.

    Returns:
        A ValidationResult; `.valid` is False if any error-severity issue was found.
    """
    result = ValidationResult()

    if resource.get("resourceType") != sd.type:
        result.issues.append(ValidationIssue(
            "error", "resourceType",
            f"Expected resourceType '{sd.type}', got {resource.get('resourceType')!r}",
        ))
        return result

    if isinstance(resource, dict):
        _validate_children(resource, sd, prefix="", result=result)
    return result


def _validate_children(container: dict, sd: StructureDefinition, prefix: str, result: ValidationResult) -> None:
    children = sd.immediate_children(prefix)
    by_path: dict[str, list[ElementDefinition]] = {}
    for el in children:
        by_path.setdefault(sd.relative_path(el), []).append(el)

    for rel_path, els in by_path.items():
        # v1 scope: slicing beyond what's needed for cardinality/type checks isn't
        # disambiguated — the first slice's constraints are used for the whole group.
        primary = els[0]
        raw_field_name = rel_path.split(".")[-1]
        values = _field_values(container, raw_field_name, primary.type_codes)
        count = len(values)

        if count < primary.min:
            result.issues.append(ValidationIssue(
                "error", rel_path, f"required (min cardinality {primary.min}) but found {count}",
            ))
        if primary.max_int is not None and count > primary.max_int:
            result.issues.append(ValidationIssue(
                "error", rel_path, f"max cardinality {primary.max} exceeded (found {count})",
            ))

        for value in values:
            _validate_value(value, primary, rel_path, result)
            if isinstance(value, dict) and sd.immediate_children(rel_path):
                _validate_children(value, sd, rel_path, result)


def _validate_value(value, el: ElementDefinition, rel_path: str, result: ValidationResult) -> None:
    if el.fixed:
        _, fixed_value = el.fixed
        if value != fixed_value:
            result.issues.append(ValidationIssue(
                "error", rel_path, f"must equal fixed value {fixed_value!r}, got {value!r}",
            ))

    if el.pattern:
        _, pattern_value = el.pattern
        if not _pattern_matches(value, pattern_value):
            result.issues.append(ValidationIssue(
                "error", rel_path, f"does not match required pattern {pattern_value!r}",
            ))

    if el.binding and el.binding.get("strength") == "required":
        value_set = el.binding.get("valueSet", "").split("|")[0]
        options = fhir_datatypes.KNOWN_VALUE_SETS.get(value_set)
        if options and isinstance(value, str) and value not in options:
            result.issues.append(ValidationIssue(
                "error", rel_path, f"{value!r} is not in required binding {value_set}",
            ))

    type_code = el.type_codes[0] if el.type_codes else None
    check = _PRIMITIVE_CHECKS.get(type_code)
    if check and not check(value):
        result.issues.append(ValidationIssue(
            "error", rel_path, f"value {value!r} is not a valid {type_code}",
        ))
