import json
from pathlib import Path

from click.testing import CliRunner

from hl7fhirgen.cli import cli

EXAMPLE_PROFILE = str(Path(__file__).resolve().parent.parent / "examples" / "patient-example-profile.json")


def test_generate_command_prints_valid_json():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", EXAMPLE_PROFILE])
    assert result.exit_code == 0, result.output
    resource = json.loads(result.output)
    assert resource["resourceType"] == "Patient"


def test_validate_command_reports_success(tmp_path):
    runner = CliRunner()
    gen_result = runner.invoke(cli, ["generate", EXAMPLE_PROFILE])
    resource_file = tmp_path / "patient.json"
    resource_file.write_text(gen_result.output, encoding="utf-8")

    result = runner.invoke(cli, ["validate", str(resource_file), "--profile", EXAMPLE_PROFILE])
    assert result.exit_code == 0, result.output
    assert "Valid against" in result.output


def test_explain_command_prints_markdown():
    runner = CliRunner()
    result = runner.invoke(cli, ["explain", EXAMPLE_PROFILE])
    assert result.exit_code == 0, result.output
    assert "# ExamplePatient" in result.output
