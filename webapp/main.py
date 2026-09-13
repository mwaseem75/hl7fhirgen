"""FastAPI playground: try hl7fhirgen in the browser, no install required."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from hl7fhirgen.explainer import explain
from hl7fhirgen.generator import generate_resource
from hl7fhirgen.packs.nphies import DISCLAIMER, check_claim, explain_rejection, list_rejection_codes
from hl7fhirgen.structure_definition import StructureDefinition, StructureDefinitionError
from hl7fhirgen.validator import validate_resource

app = FastAPI(title="hl7fhirgen playground")

STATIC_DIR = Path(__file__).parent / "static"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

EXAMPLE_FILES = {
    "patient": EXAMPLES_DIR / "patient-example-profile.json",
    "nphies-claim": EXAMPLES_DIR / "nphies" / "claim-example-profile.json",
    "nphies-claim-response": EXAMPLES_DIR / "nphies" / "claim-response-example-profile.json",
}
EXAMPLE_RESOURCE_FILES = {
    "nphies-claim-response": EXAMPLES_DIR / "nphies" / "claim-response-example.json",
}


class ProfileRequest(BaseModel):
    profile_json: str
    include_optional: bool = False


class ValidateRequest(BaseModel):
    resource_json: str
    profile_json: str


class RejectionRequest(BaseModel):
    code: str


def _load_sd(profile_json: str) -> StructureDefinition:
    try:
        return StructureDefinition.from_dict(json.loads(profile_json))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid profile JSON: {exc}")
    except StructureDefinitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def _load_resource(resource_json: str) -> dict:
    try:
        return json.loads(resource_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid resource JSON: {exc}")


@app.get("/api/examples")
def api_examples():
    return {
        "profiles": {key: path.read_text(encoding="utf-8") for key, path in EXAMPLE_FILES.items()},
        "resources": {key: path.read_text(encoding="utf-8") for key, path in EXAMPLE_RESOURCE_FILES.items()},
    }


@app.post("/api/generate")
def api_generate(req: ProfileRequest):
    sd = _load_sd(req.profile_json)
    return generate_resource(sd, include_optional=req.include_optional)


@app.post("/api/validate")
def api_validate(req: ValidateRequest):
    sd = _load_sd(req.profile_json)
    resource = _load_resource(req.resource_json)
    result = validate_resource(resource, sd)
    return {
        "valid": result.valid,
        "issues": [{"severity": i.severity, "path": i.path, "message": i.message} for i in result.issues],
    }


@app.post("/api/explain")
def api_explain(req: ProfileRequest):
    sd = _load_sd(req.profile_json)
    return {"markdown": explain(sd)}


@app.post("/api/nphies/check-claim")
def api_nphies_check_claim(req: ValidateRequest):
    sd = _load_sd(req.profile_json)
    resource = _load_resource(req.resource_json)
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


@app.post("/api/nphies/explain-rejection")
def api_nphies_explain_rejection(req: RejectionRequest):
    explanation = explain_rejection(req.code)
    if explanation is None:
        raise HTTPException(status_code=404, detail=f"{req.code!r} is not in the bundled knowledge base.")
    return {
        "title": explanation.title,
        "likely_causes": explanation.likely_causes,
        "suggested_fix": explanation.suggested_fix,
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/nphies/rejection-codes")
def api_nphies_rejection_codes():
    return {"codes": list_rejection_codes()}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
