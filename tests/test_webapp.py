"""Tests for the FastAPI playground (webapp/main.py) via FastAPI's TestClient —
no real server/socket involved.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from webapp.main import app

client = TestClient(app)


def test_serves_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "hl7fhirgen" in response.text.lower()


def test_examples_endpoint_includes_bundled_profiles():
    response = client.get("/api/examples")
    assert response.status_code == 200
    data = response.json()
    assert "patient" in data["profiles"]
    assert "nphies-claim" in data["profiles"]
    assert "nphies-claim-response" in data["resources"]


def test_generate_then_validate(patient_sd_json):
    gen_response = client.post("/api/generate", json={"profile_json": patient_sd_json, "include_optional": True})
    assert gen_response.status_code == 200
    resource = gen_response.json()
    assert resource["resourceType"] == "Patient"

    val_response = client.post("/api/validate", json={
        "resource_json": json.dumps(resource),
        "profile_json": patient_sd_json,
    })
    assert val_response.status_code == 200
    assert val_response.json()["valid"] is True


def test_generate_with_invalid_profile_returns_422(patient_sd_json):
    response = client.post("/api/generate", json={"profile_json": '{"resourceType": "Patient"}'})
    assert response.status_code == 422


def test_generate_with_malformed_json_returns_400():
    response = client.post("/api/generate", json={"profile_json": "not json"})
    assert response.status_code == 400


def test_explain_endpoint(patient_sd_json):
    response = client.post("/api/explain", json={"profile_json": patient_sd_json})
    assert response.status_code == 200
    assert "# ExamplePatient" in response.json()["markdown"]


def test_nphies_check_claim_reports_rejections(nphies_examples_dir):
    profile_json = (nphies_examples_dir / "claim-response-example-profile.json").read_text(encoding="utf-8")
    resource_json = (nphies_examples_dir / "claim-response-example.json").read_text(encoding="utf-8")

    response = client.post("/api/nphies/check-claim", json={"resource_json": resource_json, "profile_json": profile_json})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    codes = {e["code"] for e in data["rejection_explanations"]}
    assert codes == {"duplicate-claim", "missing-preauth"}
    assert "disclaimer" in data


def test_nphies_explain_rejection_known_code():
    response = client.post("/api/nphies/explain-rejection", json={"code": "duplicate-claim"})
    assert response.status_code == 200
    assert "title" in response.json()


def test_nphies_explain_rejection_unknown_code_returns_404():
    response = client.post("/api/nphies/explain-rejection", json={"code": "not-a-real-code"})
    assert response.status_code == 404


def test_nphies_rejection_codes_endpoint():
    response = client.get("/api/nphies/rejection-codes")
    assert response.status_code == 200
    assert "duplicate-claim" in response.json()["codes"]
