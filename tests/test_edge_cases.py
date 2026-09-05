"""
Edge Case & Security Tests for Polypharmacy Deprescribing Agent.
Tests boundary conditions, error handling, and security features.
"""
import os
import sys
import tempfile
from pathlib import Path

# Set required environment variable before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-edge-case-audit-key-2026")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


class TestPHIGuardEdgeCases:
    """Test PHI guard with various adversarial inputs."""

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")

    def test_mrn_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_ssn_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_number_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email patient at john@example.com")

    def test_dob_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1950")

    def test_patient_name_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 has SSN 123-45-6789")
        assert "REDACTED_IDENTIFIER" in redacted
        assert "MRN-12345678" not in redacted
        assert "123-45-6789" not in redacted

    def test_empty_string_passes(self):
        PHIGuard.assert_no_phi("")

    def test_none_handled(self):
        PHIGuard.assert_no_phi(None)


class TestWorkerBoundaryConditions:
    """Test workers at boundary values."""

    def test_qc_worker_at_threshold(self):
        # Exactly at threshold should NOT trigger
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=25.0)
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_qc_worker_just_above_threshold(self):
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=25.01)
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 1
        assert alerts[0].urgency == UrgencyLevel.ELEVATED

    def test_qc_worker_zero_value(self):
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=0.0)
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_safety_worker_critical_flag_only(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="K1",
            primary_metric=10.0, secondary_metric=1.0,
            is_critical_flag=True
        )
        alerts = SafetyEscalationWorker.evaluate(payload)
        assert len(alerts) == 1
        assert alerts[0].urgency == UrgencyLevel.CRITICAL_STAT

    def test_safety_worker_secondary_threshold(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="K1",
            primary_metric=10.0, secondary_metric=12.01
        )
        alerts = SafetyEscalationWorker.evaluate(payload)
        assert len(alerts) == 1
        assert alerts[0].urgency == UrgencyLevel.ELEVATED

    def test_conformance_worker_normal_status(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="K1",
            primary_metric=10.0, status_descriptor="NORMAL"
        )
        alerts = ProtocolConformanceWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_conformance_worker_discordant(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="K1",
            primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY"
        )
        alerts = ProtocolConformanceWorker.evaluate(payload)
        assert len(alerts) == 1

    def test_conformance_worker_fail_status(self):
        payload = SystemTaskPayload(
            task_id="T1", target_identifier="K1",
            primary_metric=10.0, status_descriptor="FAIL"
        )
        alerts = ProtocolConformanceWorker.evaluate(payload)
        assert len(alerts) == 1


class TestAuditTrailIntegrity:
    """Test HMAC audit trail integrity."""

    def test_audit_trail_chain_valid(self):
        trail = AuditTrail(secret_key="test-key-2026")
        trail.log("actor1", "tier1", "EVENT_1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_2", {"data": "value2"})
        trail.log("actor3", "tier3", "EVENT_3", {"data": "value3"})
        assert trail.verify_integrity() is True

    def test_audit_trail_not_empty_after_log(self):
        trail = AuditTrail(secret_key="test-key-2026")
        assert len(trail.get_trail()) == 0
        trail.log("actor1", "tier1", "EVENT_1", {"data": "value1"})
        assert len(trail.get_trail()) == 1

    def test_audit_trail_entries_linked(self):
        trail = AuditTrail(secret_key="test-key-2026")
        trail.log("a", "t", "E1", {"x": 1})
        trail.log("a", "t", "E2", {"x": 2})
        entries = trail.get_trail()
        assert entries[1]["prev_hash"] == entries[0]["current_hash"]

    def test_audit_trail_tamper_detected(self):
        trail = AuditTrail(secret_key="test-key-2026")
        trail.log("a", "t", "E1", {"x": 1})
        trail.log("a", "t", "E2", {"x": 2})
        # Tamper with first entry
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_requires_secret_key(self):
        # Temporarily remove env var
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(RuntimeError, match="AUDIT_SECRET_KEY"):
                AuditTrail()
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original


class TestCLIBatchErrorHandling:
    """Test CLI batch command error handling."""

    def test_batch_missing_file(self):
        result = main(["batch", "-i", "nonexistent_file_12345.csv"])
        assert result == 1

    def test_batch_with_valid_csv(self):
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n")
            f.write("TASK-001,TARGET-001,10.0,5.0,NOMINAL,false\n")
            f.write("TASK-002,TARGET-002,35.0,15.0,DISCORDANT,true\n")
            temp_path = f.name

        try:
            result = main(["batch", "-i", temp_path, "-o", "test_output.csv"])
            assert result == 0
            # Verify output file was created
            assert Path("test_output.csv").exists()
        finally:
            os.unlink(temp_path)
            if Path("test_output.csv").exists():
                os.unlink("test_output.csv")

    def test_audit_command_returns_zero(self):
        result = main(["audit", "--task-id", "TEST-EDGE-01"])
        assert result == 0

    def test_chat_command_returns_zero(self):
        result = main(["chat", "system", "status"])
        assert result == 0

    def test_verify_audit_command(self):
        result = main(["verify-audit"])
        assert result == 0


class TestSupervisorCriticalPath:
    """Test supervisor with critical and edge-case payloads."""

    def test_all_critical_workers_trigger(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="CRITICAL-ALL",
            target_identifier="KEY-CRIT",
            primary_metric=50.0,  # Triggers QC worker
            secondary_metric=20.0,  # Triggers Safety worker
            status_descriptor="DISCORDANT_ANOMALY",  # Triggers Conformance worker
            is_critical_flag=True,  # Also triggers Safety as CRITICAL_STAT
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.CRITICAL_STAT
        assert dossier.integrity_status == SystemIntegrityStatus.RECALIBRATION_REQUIRED
        assert dossier.total_alerts >= 3

    def test_nominal_payload_no_alerts(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="NOMINAL-01",
            target_identifier="KEY-NOM",
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="NORMAL",
            is_critical_flag=False,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ROUTINE
        assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
        assert dossier.total_alerts == 0
