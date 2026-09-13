from __future__ import annotations

import json
from pathlib import Path

import click

from hl7fhirgen.explainer import explain
from hl7fhirgen.generator import generate_resource
from hl7fhirgen.packs.nphies import DISCLAIMER, check_claim, explain_rejection, list_rejection_codes
from hl7fhirgen.structure_definition import StructureDefinitionError, load_structure_definition
from hl7fhirgen.validator import validate_resource


@click.group()
@click.version_option()
def cli():
    """hl7FHIRGen — generate, validate, and explain FHIR resources against any StructureDefinition profile."""


@cli.command()
@click.argument("profile", type=click.Path(exists=True, dir_okay=False))
@click.option("--full", is_flag=True, help="Also populate optional elements, not just required/must-support ones.")
@click.option("--out", "out_file", type=click.Path(), default=None,
              help="File to write the generated resource JSON to. Prints to stdout if omitted.")
def generate(profile, full, out_file):
    """Generate a synthetic resource conforming to PROFILE (a StructureDefinition JSON file)."""
    try:
        sd = load_structure_definition(profile)
    except StructureDefinitionError as exc:
        raise click.ClickException(str(exc))

    resource = generate_resource(sd, include_optional=full)
    output = json.dumps(resource, indent=2, default=str)
    if out_file:
        Path(out_file).write_text(output, encoding="utf-8")
        click.echo(f"Wrote {out_file}")
    else:
        click.echo(output)


@cli.command()
@click.argument("resource_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--profile", required=True, type=click.Path(exists=True, dir_okay=False),
              help="StructureDefinition JSON file to validate against.")
def validate(resource_file, profile):
    """Validate RESOURCE_FILE (a FHIR resource JSON file) against --profile."""
    try:
        sd = load_structure_definition(profile)
    except StructureDefinitionError as exc:
        raise click.ClickException(str(exc))

    resource = json.loads(Path(resource_file).read_text(encoding="utf-8"))
    result = validate_resource(resource, sd)

    if result.valid:
        click.echo(f"Valid against {sd.name}.")
        return

    for issue in result.issues:
        click.echo(f"[{issue.severity.upper()}] {issue.path}: {issue.message}")
    raise click.exceptions.Exit(1)


@cli.command("explain")
@click.argument("profile", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "out_file", type=click.Path(), default=None,
              help="File to write the markdown summary to. Prints to stdout if omitted.")
def explain_cmd(profile, out_file):
    """Print a plain-English markdown summary of PROFILE (a StructureDefinition JSON file)."""
    try:
        sd = load_structure_definition(profile)
    except StructureDefinitionError as exc:
        raise click.ClickException(str(exc))

    summary = explain(sd)
    if out_file:
        Path(out_file).write_text(summary, encoding="utf-8")
        click.echo(f"Wrote {out_file}")
    else:
        click.echo(summary)


@cli.group()
def nphies():
    """NPHIES pack: pre-submission claim checking and rejection-code lookups.

    See CONTRIBUTING.md / hl7fhirgen.packs.nphies docstring for what this is (and
    isn't) sourced from before relying on it for a real claim.
    """


@nphies.command("check-claim")
@click.argument("resource_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--profile", required=True, type=click.Path(exists=True, dir_okay=False),
              help="StructureDefinition JSON file to validate against (e.g. your own NPHIES profile).")
def nphies_check_claim(resource_file, profile):
    """Validate RESOURCE_FILE against --profile and explain any recognized rejection codes."""
    try:
        sd = load_structure_definition(profile)
    except StructureDefinitionError as exc:
        raise click.ClickException(str(exc))

    resource = json.loads(Path(resource_file).read_text(encoding="utf-8"))
    result, explanations = check_claim(resource, sd)

    if result.valid:
        click.echo(f"Valid against {sd.name}.")
    else:
        for issue in result.issues:
            click.echo(f"[{issue.severity.upper()}] {issue.path}: {issue.message}")

    if explanations:
        click.echo("")
        click.echo(f"Recognized rejection codes ({DISCLAIMER}):")
        for exp in explanations:
            click.echo(f"\n- {exp.code}: {exp.title}")
            for cause in exp.likely_causes:
                click.echo(f"    - {cause}")
            click.echo(f"  Suggested fix: {exp.suggested_fix}")

    if not result.valid:
        raise click.exceptions.Exit(1)


@nphies.command("explain-rejection")
@click.argument("code")
def nphies_explain_rejection(code):
    """Explain a rejection-pattern CODE (see `nphies list-rejections` for known codes)."""
    explanation = explain_rejection(code)
    if explanation is None:
        raise click.ClickException(
            f"{code!r} is not in the bundled knowledge base. Run 'hl7fhirgen nphies list-rejections' "
            "to see what's covered, or contribute it via a PR (see CONTRIBUTING.md)."
        )
    click.echo(f"{explanation.title}\n")
    click.echo("Likely causes:")
    for cause in explanation.likely_causes:
        click.echo(f"  - {cause}")
    click.echo(f"\nSuggested fix: {explanation.suggested_fix}")
    click.echo(f"\n({DISCLAIMER})")


@nphies.command("list-rejections")
def nphies_list_rejections():
    """List all rejection-pattern codes in the bundled knowledge base."""
    for code in list_rejection_codes():
        click.echo(code)


if __name__ == "__main__":
    cli()
