"""MCP server exposing hl7fhirgen's core library as tools an MCP client can call.

Runs locally over stdio: an MCP client (Claude Desktop, Claude Code, etc.) launches
this script as a child process and talks to it over stdin/stdout using the MCP
protocol. Tools take StructureDefinition/resource JSON as strings (not file paths)
so they work regardless of what filesystem access the calling client has.

All tools are read-only and side-effect-free — nothing here submits data anywhere.
"""
from __future__ import annotations

import json

from mcp.server import MCPServer

from hl7fhirgen.explainer import explain
from hl7fhirgen.generator import generate_resource
from hl7fhirgen.packs.nphies import DISCLAIMER, check_claim, explain_rejection, list_rejection_codes
from hl7fhirgen.structure_definition import StructureDefinition, StructureDefinitionError
from hl7fhirgen.validator import validate_resource

mcp = MCPServer(name="hl7fhirgen", version="0.1.0")


def _load_sd(profile_json: str) -> StructureDefinition:
    return StructureDefinition.from_dict(json.loads(profile_json))


@mcp.tool()
def generate_fhir_resource(profile_json: str, include_optional: bool = False) -> dict:
    """Generate a synthetic FHIR resource conforming to a StructureDefinition.

    Args:
        profile_json: The StructureDefinition, as a JSON string.
        include_optional: If true, also populate optional elements (not just
            required/must-support ones).

    Returns:
        The generated resource as a dict, or {"error": str} if the profile is invalid.
    """
    try:
        sd = _load_sd(profile_json)
    except (StructureDefinitionError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}
    return generate_resource(sd, include_optional=include_optional)


@mcp.tool()
def validate_fhir_resource(resource_json: str, profile_json: str) -> dict:
    """Validate a FHIR resource against a StructureDefinition.

    Checks a documented subset of full FHIR conformance: cardinality, fixed/pattern
    values, required-strength bindings for well-known value sets, and basic
    primitive-type sanity. Not a replacement for the official HL7 FHIR validator.

    Args:
        resource_json: The FHIR resource to validate, as a JSON string.
        profile_json: The StructureDefinition to validate against, as a JSON string.

    Returns:
        {"valid": bool, "issues": [{"severity", "path", "message"}, ...]}, or
        {"error": str} if the resource or profile JSON is invalid.
    """
    try:
        sd = _load_sd(profile_json)
        resource = json.loads(resource_json)
    except (StructureDefinitionError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}
    result = validate_resource(resource, sd)
    return {
        "valid": result.valid,
        "issues": [{"severity": i.severity, "path": i.path, "message": i.message} for i in result.issues],
    }


@mcp.tool()
def explain_profile(profile_json: str) -> str:
    """Summarize a StructureDefinition as plain-English markdown.

    Args:
        profile_json: The StructureDefinition, as a JSON string.
    """
    try:
        sd = _load_sd(profile_json)
    except (StructureDefinitionError, json.JSONDecodeError) as exc:
        return f"Error: {exc}"
    return explain(sd)


@mcp.tool()
def nphies_check_claim(resource_json: str, profile_json: str) -> dict:
    """Validate a claim/eligibility-shaped resource and explain any recognized rejection codes.

    See the NPHIES pack's disclaimer in the result — the rejection-code knowledge
    base is community-sourced and illustrative, not an official NPHIES source.

    Args:
        resource_json: A Claim/ClaimResponse-shaped FHIR resource, as a JSON string.
        profile_json: The StructureDefinition to validate against, as a JSON string.

    Returns:
        {"valid", "issues", "rejection_explanations": [{"code","title",
        "likely_causes","suggested_fix"}, ...], "disclaimer"}, or {"error": str}.
    """
    try:
        sd = _load_sd(profile_json)
        resource = json.loads(resource_json)
    except (StructureDefinitionError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}
    result, explanations = check_claim(resource, sd)
    return {
        "valid": result.valid,
        "issues": [{"severity": i.severity, "path": i.path, "message": i.message} for i in result.issues],
        "rejection_explanations": [
            {"code": e.code, "title": e.title, "likely_causes": e.likely_causes, "suggested_fix": e.suggested_fix}
            for e in explanations
        ],
        "disclaimer": DISCLAIMER,
    }


@mcp.tool()
def nphies_explain_rejection(code: str) -> dict:
    """Look up a rejection-pattern code in the bundled (illustrative) knowledge base.

    Args:
        code: A rejection-pattern slug, e.g. "duplicate-claim" — see
            `nphies_list_rejection_codes` for what's covered.

    Returns:
        {"title","likely_causes","suggested_fix","disclaimer"}, or {"error": str}
        if the code isn't in the knowledge base.
    """
    explanation = explain_rejection(code)
    if explanation is None:
        return {"error": f"{code!r} is not in the bundled knowledge base."}
    return {
        "title": explanation.title,
        "likely_causes": explanation.likely_causes,
        "suggested_fix": explanation.suggested_fix,
        "disclaimer": DISCLAIMER,
    }


@mcp.tool()
def nphies_list_rejection_codes() -> dict:
    """List all rejection-pattern codes in the bundled knowledge base.

    Returns:
        {"codes": [str, ...]}
    """
    return {"codes": list_rejection_codes()}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
