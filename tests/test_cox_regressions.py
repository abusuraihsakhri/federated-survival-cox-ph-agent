"""Numerical, privacy-boundary, and regression tests for Cox estimation."""
import math
import pytest
from fed_cox_ph.cox import CoxSite, fit_federated_cox
from agents.base import AuditTrail
from fed_cox_ph import agents as legacy_agents
from agents.supervisor import SystemSupervisor
from agents.models import SystemTaskPayload
from agents.base import SecurityException
from cli import parse_csv_bool

ROWS = [
    dict(time=1, event=1, covariates=[0.0]),
    dict(time=1, event=1, covariates=[1.0]),
    dict(time=2, event=0, covariates=[0.0]),
    dict(time=3, event=1, covariates=[1.0]),
    dict(time=3, event=0, covariates=[0.0]),
    dict(time=4, event=1, covariates=[1.0]),
    dict(time=5, event=0, covariates=[0.0]),
    dict(time=6, event=1, covariates=[1.0]),
    dict(time=7, event=0, covariates=[0.0]),
]


def pooled_breslow_loglik(coefficient):
    """Independent reference calculation, directly from the partial likelihood."""
    total = 0.0
    for t in sorted({r["time"] for r in ROWS if r["event"]}):
        events = [r for r in ROWS if r["time"] == t and r["event"]]
        risk = [r for r in ROWS if r["time"] >= t]
        total += sum(coefficient * r["covariates"][0] for r in events)
        total -= len(events) * math.log(
            sum(math.exp(coefficient * r["covariates"][0]) for r in risk))
    return total


def test_federated_breslow_matches_pooled_reference():
    result = fit_federated_cox([CoxSite(ROWS[:4]), CoxSite(ROWS[4:])])
    assert result.converged
    assert result.coefficients[0] == pytest.approx(1.4791397, abs=2e-5)
    assert result.log_partial_likelihood == pytest.approx(
        pooled_breslow_loglik(result.coefficients[0]), abs=1e-9)
    assert result.hazard_ratios[0] == pytest.approx(math.exp(result.coefficients[0]))
    assert result.events == 5 and result.observations == 9 and result.sites == 2


def test_site_partition_invariance_and_strata():
    one = fit_federated_cox([CoxSite(ROWS)])
    two = fit_federated_cox([CoxSite(ROWS[:5]), CoxSite(ROWS[5:])])
    assert one.coefficients == pytest.approx(two.coefficients, abs=1e-9)
    rows = [dict(r, stratum="A" if i < 4 else "B") for i, r in enumerate(ROWS)]
    stratified = fit_federated_cox([CoxSite(rows[:4]), CoxSite(rows[4:])], ridge=0.4)
    assert stratified.converged and stratified.strata == 2


def test_reject_invalid_or_unidentifiable_cox_inputs():
    with pytest.raises(ValueError, match="non-negative"):
        CoxSite([dict(time=-1, event=1, covariates=[1])])
    with pytest.raises(ValueError, match="event"):
        CoxSite([dict(time=1, event=2, covariates=[1])])
    with pytest.raises(ValueError, match="finite"):
        CoxSite([dict(time=1, event=1, covariates=[float("nan")])])
    with pytest.raises(ValueError, match="event"):
        fit_federated_cox([CoxSite([dict(time=1, event=0, covariates=[1])])])
    with pytest.raises(ValueError, match="singular"):
        fit_federated_cox([CoxSite([
            dict(time=1, event=1, covariates=[1]),
            dict(time=2, event=0, covariates=[1])])])


def test_audit_detects_tampering_not_just_chain_breaks():
    audit = AuditTrail(secret_key="unit-test-signing-key")
    entry = audit.log("tester", "unit", "test", {"status": "SUCCESS"})
    assert audit.verify_integrity()
    entry["actor"] = "altered"
    assert not audit.verify_integrity()
    entry["actor"] = "tester"
    assert audit.verify_integrity()
    entry["current_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_secondary_audit_detects_tampering():
    start = len(legacy_agents._AUDIT_LOG)
    try:
        legacy_agents._record_audit("tester", "TEST", {"status": "ok"})
        assert legacy_agents.verify_audit_integrity()
        legacy_agents._AUDIT_LOG[-1]["actor"] = "altered"
        assert not legacy_agents.verify_audit_integrity()
    finally:
        del legacy_agents._AUDIT_LOG[start:]


def test_supervisor_rejects_phi_inside_attributes():
    payload = SystemTaskPayload(task_id="TASK-01", target_identifier="KEY-01",
                                primary_metric=3.0,
                                attributes={"extra": "MRN-123456"})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


@pytest.mark.parametrize("raw,expected", [
    ("False", False), ("0", False), ("", False), ("TRUE", True), ("1", True), ("yes", True)])
def test_csv_boolean_parse(raw, expected):
    assert parse_csv_bool(raw) is expected


def test_csv_boolean_rejects_unknown():
    with pytest.raises(ValueError, match="Invalid"):
        parse_csv_bool("maybe")
