"""End-to-end test: spawns the MCP server as a real subprocess over stdio and calls
each tool through an MCP client session, the same way Claude Desktop/Code would.
"""
import json
import sys
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
NPHIES_EXAMPLES_DIR = EXAMPLES_DIR / "nphies"
PATIENT_PROFILE = (EXAMPLES_DIR / "patient-example-profile.json").read_text(encoding="utf-8")
CLAIM_RESPONSE_PROFILE = (NPHIES_EXAMPLES_DIR / "claim-response-example-profile.json").read_text(encoding="utf-8")
CLAIM_RESPONSE_RESOURCE = (NPHIES_EXAMPLES_DIR / "claim-response-example.json").read_text(encoding="utf-8")


@pytest.fixture
def server_params():
    return StdioServerParameters(command=sys.executable, args=["-m", "hl7fhirgen.mcp_server"])


async def _call(server_params, name, arguments):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            return result.content[0].text


@pytest.mark.asyncio
async def test_lists_expected_tools(server_params):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names == {
                "generate_fhir_resource",
                "validate_fhir_resource",
                "explain_profile",
                "nphies_check_claim",
                "nphies_explain_rejection",
                "nphies_list_rejection_codes",
            }


@pytest.mark.asyncio
async def test_generate_then_validate(server_params):
    resource = json.loads(await _call(server_params, "generate_fhir_resource", {"profile_json": PATIENT_PROFILE}))
    assert resource["resourceType"] == "Patient"

    result = json.loads(await _call(
        server_params, "validate_fhir_resource",
        {"resource_json": json.dumps(resource), "profile_json": PATIENT_PROFILE},
    ))
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_explain_profile(server_params):
    summary = await _call(server_params, "explain_profile", {"profile_json": PATIENT_PROFILE})
    assert "# ExamplePatient" in summary


@pytest.mark.asyncio
async def test_nphies_check_claim_reports_rejections(server_params):
    result = json.loads(await _call(
        server_params, "nphies_check_claim",
        {"resource_json": CLAIM_RESPONSE_RESOURCE, "profile_json": CLAIM_RESPONSE_PROFILE},
    ))
    assert result["valid"] is True
    codes = {e["code"] for e in result["rejection_explanations"]}
    assert codes == {"duplicate-claim", "missing-preauth"}
    assert "disclaimer" in result


@pytest.mark.asyncio
async def test_nphies_explain_rejection_known_code(server_params):
    result = json.loads(await _call(server_params, "nphies_explain_rejection", {"code": "duplicate-claim"}))
    assert "title" in result


@pytest.mark.asyncio
async def test_nphies_explain_rejection_unknown_code_returns_error(server_params):
    result = json.loads(await _call(server_params, "nphies_explain_rejection", {"code": "not-a-real-code"}))
    assert "error" in result


@pytest.mark.asyncio
async def test_nphies_list_rejection_codes(server_params):
    result = json.loads(await _call(server_params, "nphies_list_rejection_codes", {}))
    assert "duplicate-claim" in result["codes"]
