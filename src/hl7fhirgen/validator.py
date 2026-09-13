"""Validates a FHIR resource (as a dict) against a StructureDefinition.

Checks cardinality, fixed/pattern values, required-strength bindings against
the small set of value sets `fhir_datatypes.KNOWN_VALUE_SETS` ships, and basic
primitive-type sanity. This is a documented subset of full FHIR conformance
checking (no terminology server, no cross-element invariants/slicing
discriminators) — see README "Scope". Use `--strict` (shells out to the
official HL7 validator, when installed) for authoritative validation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from hl7fhirgen import fhir_datatypes
from hl7fhirgen.structure_definition import StructureDefinition

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


def _walk_path(node, segments: list[str]) -> list:
    if not segments:
        return [node]
    seg, rest = segments[0], segments[1:]
    if isinstance(node, list):
        found = []
        for item in node:
            found.extend(_walk_path(item, segments))
        return found
    if isinstance(node, dict):
        if seg not in node:
            return []
        return _walk_path(node[seg], rest)
    return []


def _pattern_matches(actual, pattern) -> bool:
    if isinstance(pattern, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and _pattern_matches(actual[k], v) for k, v in pattern.items())
    return actual == pattern


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

    for el in sd.elements:
        rel_path = sd.relative_path(el)
        if not rel_path:
            continue
        segments = rel_path.split(".")
        values = _walk_path(resource, segments)
        count = len(values)

        if count < el.min:
            result.issues.append(ValidationIssue(
                "error", rel_path, f"required (min cardinality {el.min}) but found {count}",
            ))
        if el.max_int is not None and count > el.max_int:
            result.issues.append(ValidationIssue(
                "error", rel_path, f"max cardinality {el.max} exceeded (found {count})",
            ))

        if el.fixed:
            _, fixed_value = el.fixed
            for v in values:
                if v != fixed_value:
                    result.issues.append(ValidationIssue(
                        "error", rel_path, f"must equal fixed value {fixed_value!r}, got {v!r}",
                    ))

        if el.pattern:
            _, pattern_value = el.pattern
            for v in values:
                if not _pattern_matches(v, pattern_value):
                    result.issues.append(ValidationIssue(
                        "error", rel_path, f"does not match required pattern {pattern_value!r}",
                    ))

        if el.binding and el.binding.get("strength") == "required":
            value_set = el.binding.get("valueSet", "").split("|")[0]
            options = fhir_datatypes.KNOWN_VALUE_SETS.get(value_set)
            if options:
                for v in values:
                    if isinstance(v, str) and v not in options:
                        result.issues.append(ValidationIssue(
                            "error", rel_path, f"{v!r} is not in required binding {value_set}",
                        ))

        type_code = el.type_codes[0] if el.type_codes else None
        check = _PRIMITIVE_CHECKS.get(type_code)
        if check:
            for v in values:
                if not check(v):
                    result.issues.append(ValidationIssue(
                        "error", rel_path, f"value {v!r} is not a valid {type_code}",
                    ))

    return result
