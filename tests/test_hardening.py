"""Regression tests for audit, API and CSV parsing."""
import os
os.environ.setdefault("AUDIT_SECRET_KEY", "test-only-hardened-audit-key")

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from agents.base import AuditTrail, SecurityException
from agents.api import app
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import parse_csv_bool as parse_generic_bool
from polypharmacy_deprescribing_agent.cli import parse_csv_bool as parse_clinical_bool
from deprescribe_mind import parse_bool as parse_standalone_bool


@pytest.mark.parametrize("parser", [parse_generic_bool, parse_clinical_bool, parse_standalone_bool])
def test_csv_boolean_values(parser):
    assert parser("False") is False
    assert parser("0") is False
    assert parser("yes") is True
    assert parser(True) is True
    with pytest.raises(ValueError):
        parser("sometimes")


def test_hmac_rejects_single_entry_metadata_tampering():
    audit = AuditTrail("test-secret")
    audit.log("operator", "staff", "EVALUATE", {"case": "SYNTH"})
    assert audit.verify_integrity()
    audit.logs[0]["event_type"] = "MODIFIED"
    assert audit.verify_integrity() is False


def test_audit_snapshot_is_not_mutable_internal_state():
    audit = AuditTrail("test-secret")
    audit.log("operator", "staff", "EVALUATE", {"case": "SYNTH"})
    snapshot = audit.get_trail()
    snapshot[0]["event_type"] = "MODIFIED"
    assert audit.verify_integrity()


def test_phi_in_metadata_is_rejected_before_logging():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(task_id="SYNTH", target_identifier="SYNTH-01", primary_metric=1.0,
                                attributes={"extra": {"contact": "alice@example.com"}})
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_metrics_rejected(bad):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="SYNTH", target_identifier="SYNTH-01", primary_metric=bad)


def test_api_rejects_identifier_without_500():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "SYNTH", "target_identifier": "SYNTH-01", "primary_metric": 1,
        "attributes": {"contact": "jane@example.com"}
    })
    assert response.status_code == 400
    assert "jane@example.com" not in response.text


def test_audit_logs_require_explicit_token(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("AUDIT_LOG_READ_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 404
    monkeypatch.setenv("AUDIT_LOG_READ_TOKEN", "test-only-secret")
    assert client.get("/api/audit/logs").status_code == 401
    response = client.get("/api/audit/logs", headers={"Authorization": "Bearer test-only-secret"})
    assert response.status_code == 200
    assert response.json()["verified"] is True
