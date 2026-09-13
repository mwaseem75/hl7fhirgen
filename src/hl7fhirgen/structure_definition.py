"""Parses FHIR StructureDefinition JSON into a small internal model.

Scope (see README "Scope" section): reads `snapshot.element` when present (the
normal case for any profile downloaded from an IG, Simplifier, or an authoring
tool), falling back to `differential.element` with a warning otherwise, since
merging a differential onto its base definition recursively is out of scope
for v1.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class StructureDefinitionError(ValueError):
    pass


CHOICE_SUFFIX = "[x]"


def choice_field_name(base: str, type_code: str) -> str:
    """Resolve a FHIR choice-type element (e.g. "value[x]") to its concrete JSON key.

    FHIR never serializes a literal "[x]" — a `value[x]` element typed `string` is
    serialized as `valueString`, typed `CodeableConcept` as `valueCodeableConcept`, etc.

    Args:
        base: The element name with "[x]" stripped, e.g. "value" or "diagnosis".
        type_code: The concrete FHIR type, e.g. "string", "CodeableConcept".
    """
    return f"{base}{type_code[0].upper()}{type_code[1:]}"


@dataclass
class ElementDefinition:
    """One parsed FHIR `ElementDefinition` from a StructureDefinition's snapshot/differential.

    Attributes:
        id: The element's `id` (includes slice names, e.g. "Patient.extension:birthPlace").
        path: The element's `path` (no slice names, e.g. "Patient.extension").
        slice_name: The `sliceName`, if this element is one named slice of a repeating element.
        min: Minimum cardinality.
        max: Maximum cardinality as FHIR encodes it: a digit string, or "*" for unbounded.
        types: Raw `type` array entries, e.g. `[{"code": "HumanName"}]`.
        short: The human-readable `short` description, if present.
        must_support: Whether the profile flags this element `mustSupport`.
        fixed: `(type_suffix, value)` extracted from a `fixed[x]` key, e.g. `("Uri", "...")`.
        pattern: `(type_suffix, value)` extracted from a `pattern[x]` key.
        binding: The raw `binding` object (`{"strength": ..., "valueSet": ...}`), if present.
    """

    id: str
    path: str
    slice_name: str | None
    min: int
    max: str
    types: list[dict[str, Any]]
    short: str | None
    must_support: bool
    fixed: tuple[str, Any] | None
    pattern: tuple[str, Any] | None
    binding: dict[str, Any] | None

    @property
    def max_is_unbounded(self) -> bool:
        return self.max == "*"

    @property
    def max_int(self) -> int | None:
        return None if self.max_is_unbounded else int(self.max)

    @property
    def is_required(self) -> bool:
        return self.min >= 1

    @property
    def type_codes(self) -> list[str]:
        return [t.get("code", "") for t in self.types]


def _relative_path(path: str, resource_type: str) -> str:
    prefix = resource_type + "."
    return path[len(prefix):] if path.startswith(prefix) else ""


def _extract_value_prefixed(el: dict, prefix: str) -> tuple[str, Any] | None:
    """Find a FHIR `fixed[x]`/`pattern[x]` key (e.g. "fixedString", "patternCodeableConcept")."""
    for key, value in el.items():
        if key.startswith(prefix) and len(key) > len(prefix):
            return key[len(prefix):], value
    return None


def _parse_element(el: dict, resource_type: str) -> ElementDefinition:
    element_id = el.get("id", el["path"])
    slice_name = el.get("sliceName")
    return ElementDefinition(
        id=element_id,
        path=el["path"],
        slice_name=slice_name,
        min=int(el.get("min", 0)),
        max=str(el.get("max", "1")),
        types=el.get("type", []),
        short=el.get("short"),
        must_support=bool(el.get("mustSupport", False)),
        fixed=_extract_value_prefixed(el, "fixed"),
        pattern=_extract_value_prefixed(el, "pattern"),
        binding=el.get("binding"),
    )


@dataclass
class StructureDefinition:
    """A parsed FHIR `StructureDefinition`, exposing its elements as a flat list plus
    convenience queries (`required_elements`, `must_support_elements`, etc.) used by
    the generator, validator, and explainer.

    Attributes:
        url: The profile's canonical URL.
        name: The profile's `name`.
        type: The base FHIR resource type this profile constrains, e.g. "Patient".
        status: The profile's publication `status` ("draft", "active", ...).
        description: The profile's `description`, if present.
        elements: All non-root `ElementDefinition`s, in document order.
        used_fallback_differential: True if no `snapshot` was present and `differential`
            was used instead — inherited base elements not listed there won't appear.
    """

    url: str
    name: str
    type: str
    status: str
    description: str | None
    elements: list[ElementDefinition] = field(default_factory=list)
    used_fallback_differential: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "StructureDefinition":
        """Parse a `StructureDefinition` resource (already loaded as a dict) into this model.

        Raises:
            StructureDefinitionError: if `d` isn't a StructureDefinition, is missing
                its `type`, or has neither `snapshot.element` nor `differential.element`.
        """
        if d.get("resourceType") != "StructureDefinition":
            raise StructureDefinitionError(
                f"Expected resourceType 'StructureDefinition', got {d.get('resourceType')!r}"
            )
        resource_type = d.get("type")
        if not resource_type:
            raise StructureDefinitionError("StructureDefinition is missing required field 'type'")

        used_fallback = False
        raw_elements = (d.get("snapshot") or {}).get("element")
        if not raw_elements:
            raw_elements = (d.get("differential") or {}).get("element")
            used_fallback = True
        if not raw_elements:
            raise StructureDefinitionError(
                "StructureDefinition has neither snapshot.element nor differential.element"
            )

        elements = [
            _parse_element(el, resource_type)
            for el in raw_elements
            if el.get("path") != resource_type  # skip the root element itself
        ]

        return cls(
            url=d.get("url", ""),
            name=d.get("name", resource_type),
            type=resource_type,
            status=d.get("status", "unknown"),
            description=d.get("description"),
            elements=elements,
            used_fallback_differential=used_fallback,
        )

    def relative_path(self, el: ElementDefinition) -> str:
        """`el.path` with the leading "{ResourceType}." prefix stripped, e.g. "name.family"."""
        return _relative_path(el.path, self.type)

    def immediate_children(self, prefix: str) -> list[ElementDefinition]:
        """Elements exactly one path segment below `prefix` (""=top level).

        Used by the generator and explainer to walk the element tree depth-by-depth
        without needing a fully nested tree structure.
        """
        target_depth = 1 if prefix == "" else len(prefix.split(".")) + 1
        result = []
        for el in self.elements:
            rel = self.relative_path(el)
            if not rel:
                continue
            segments = rel.split(".")
            if len(segments) != target_depth:
                continue
            if prefix and not rel.startswith(prefix + "."):
                continue
            result.append(el)
        return result

    def required_elements(self) -> list[ElementDefinition]:
        """All elements with `min >= 1` (excluding the resource root)."""
        return [el for el in self.elements if el.is_required and self.relative_path(el)]

    def must_support_elements(self) -> list[ElementDefinition]:
        """All elements flagged `mustSupport` (excluding the resource root)."""
        return [el for el in self.elements if el.must_support and self.relative_path(el)]

    def extension_slices(self) -> list[ElementDefinition]:
        """All named extension slices (elements ending in `.extension` with a `sliceName`)."""
        return [
            el for el in self.elements
            if el.slice_name and self.relative_path(el).split(".")[-1] == "extension"
        ]

    def bound_elements(self) -> list[ElementDefinition]:
        """All elements that carry a terminology `binding` (any strength)."""
        return [el for el in self.elements if el.binding and self.relative_path(el)]

    def constrained_elements(self) -> list[ElementDefinition]:
        """All elements with a `fixed[x]` or `pattern[x]` constraint."""
        return [el for el in self.elements if (el.fixed or el.pattern) and self.relative_path(el)]


def load_structure_definition(source: str) -> StructureDefinition:
    """Load and parse a StructureDefinition from a local file path or an http(s) URL.

    Args:
        source: A filesystem path, or a URL starting with "http://"/"https://".

    Returns:
        The parsed StructureDefinition.

    Raises:
        StructureDefinitionError: if the loaded JSON isn't a valid StructureDefinition.
        OSError: if a local file can't be read.
        urllib.error.URLError: if a URL can't be fetched.
    """
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=30) as resp:  # noqa: S310 - explicit http(s) only
            raw = resp.read().decode("utf-8")
    else:
        raw = Path(source).read_text(encoding="utf-8")
    return StructureDefinition.from_dict(json.loads(raw))
