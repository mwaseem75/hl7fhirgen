"""Turns a StructureDefinition into a plain-English markdown summary."""
from __future__ import annotations

from hl7fhirgen.structure_definition import StructureDefinition


def explain(sd: StructureDefinition) -> str:
    """Render `sd` as a plain-English markdown summary.

    Args:
        sd: The profile to summarize.

    Returns:
        A markdown string with sections for required elements, must-support
        elements, extensions, value-set bindings, and fixed/pattern values.
    """
    lines = [f"# {sd.name} ({sd.type})"]
    if sd.url:
        lines.append(f"`{sd.url}`")
    if sd.description:
        lines += ["", sd.description]

    if sd.used_fallback_differential:
        lines += ["", "> Note: this StructureDefinition has no `snapshot`, only a `differential` — "
                       "inherited base elements not listed here are not shown."]

    required = sd.required_elements()
    lines += ["", "## Required elements"]
    if required:
        for el in sorted(required, key=lambda e: sd.relative_path(e)):
            lines.append(_element_line(sd, el))
    else:
        lines.append("_None._")

    must_support = [el for el in sd.must_support_elements() if not el.is_required]
    lines += ["", "## Must-support elements"]
    if must_support:
        for el in sorted(must_support, key=lambda e: sd.relative_path(e)):
            lines.append(_element_line(sd, el))
    else:
        lines.append("_None._")

    extensions = sd.extension_slices()
    lines += ["", "## Extensions"]
    if extensions:
        for el in extensions:
            profile = el.types[0].get("profile", [None])[0] if el.types else None
            target = profile or el.slice_name
            req = "required" if el.is_required else "optional"
            lines.append(f"- **{el.slice_name}** ({req}) — `{target}`")
    else:
        lines.append("_None._")

    bindings = [el for el in sd.bound_elements() if el.binding.get("strength") in ("required", "extensible")]
    lines += ["", "## Value set bindings"]
    if bindings:
        for el in sorted(bindings, key=lambda e: sd.relative_path(e)):
            strength = el.binding.get("strength")
            vs = el.binding.get("valueSet")
            lines.append(f"- `{sd.relative_path(el)}` — **{strength}**: {vs}")
    else:
        lines.append("_None._")

    constrained = sd.constrained_elements()
    lines += ["", "## Fixed / pattern values"]
    if constrained:
        for el in sorted(constrained, key=lambda e: sd.relative_path(e)):
            kind, (suffix, value) = ("fixed", el.fixed) if el.fixed else ("pattern", el.pattern)
            lines.append(f"- `{sd.relative_path(el)}` — {kind} to `{value}`")
    else:
        lines.append("_None._")

    return "\n".join(lines) + "\n"


def _element_line(sd: StructureDefinition, el) -> str:
    card = f"{el.min}..{el.max}"
    types = ", ".join(el.type_codes) or "?"
    short = f" — {el.short}" if el.short else ""
    return f"- `{sd.relative_path(el)}` [{card}] ({types}){short}"
