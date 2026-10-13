"""
Distributed Component Coordination & Executive Hierarchy for FedCox-PH: Federated Stratified Cox Proportional Hazards Regression Agent.
Domain: Privacy-Preserving Federated Healthcare & FHE
"""
import uuid
import hashlib
import hmac
import os
import warnings
import secrets
import json
import copy
from typing import Dict, Any, List, Optional
from .models import FrontierPayload, AgentTelemetryAlert, ExecutionStatus
from .engine import FrontierDomainEngine

# ---------------------------------------------------------------------------
# HMAC-SHA256 Audit Trail (FedCox-PH local)
# ---------------------------------------------------------------------------
_AUDIT_KEY = os.getenv("AUDIT_SECRET_KEY", "").encode("utf-8")
if not _AUDIT_KEY:
    warnings.warn(
        "AUDIT_SECRET_KEY not set for FedCox-PH; using process-local random audit key.",
        RuntimeWarning,
        stacklevel=1,
    )
    _AUDIT_KEY = secrets.token_bytes(32)

_AUDIT_LOG: List[Dict[str, Any]] = []


def _record_audit(actor: str, event_type: str, details: Dict[str, Any]) -> str:
    payload_str = json.dumps(details, sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    prev_hash = _AUDIT_LOG[-1]["current_hash"] if _AUDIT_LOG else "GENESIS"
    sign_data = f"{actor}|{event_type}|{payload_hash}|{prev_hash}"
    signature = hmac.new(_AUDIT_KEY, sign_data.encode("utf-8"), hashlib.sha256).hexdigest()
    entry = {"actor": actor, "event_type": event_type, "payload_hash": payload_hash,
             "prev_hash": prev_hash, "current_hash": signature}
    _AUDIT_LOG.append(entry)
    return signature


def verify_audit_integrity() -> bool:
    prev = "GENESIS"
    for entry in _AUDIT_LOG:
        try:
            if entry["prev_hash"] != prev:
                return False
            data = f'{entry["actor"]}|{entry["event_type"]}|{entry["payload_hash"]}|{entry["prev_hash"]}'
            expected = hmac.new(_AUDIT_KEY, data.encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(entry["current_hash"], expected):
                return False
            prev = entry["current_hash"]
        except (KeyError, TypeError, AttributeError):
            return False
    return True


def get_audit_trail() -> List[Dict[str, Any]]:
    return copy.deepcopy(_AUDIT_LOG)


class LocalGradientHessianAgent:
    """Specialized Sub-Agent 1: Primary Parameter & Integrity Auditor."""
    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.evaluate_primary_parameter(payload.primary_metric)
        if res:
            alerts.append(AgentTelemetryAlert(
                alert_id=str(uuid.uuid4())[:8],
                origin_agent="LocalGradientHessianAgent",
                status=ExecutionStatus.ELEVATED_RISK,
                summary=res["summary"],
                technical_details=res["details"],
                actionable_remediation=res["remediation"],
            ))
        return alerts


class CentralAggregatorAgent:
    """Specialized Sub-Agent 2: Critical Kinetics & Security Safeguard."""
    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.evaluate_secondary_kinetics(payload.secondary_metric, payload.is_critical_flag)
        if res:
            alerts.append(AgentTelemetryAlert(
                alert_id=str(uuid.uuid4())[:8],
                origin_agent="CentralAggregatorAgent",
                status=ExecutionStatus.CRITICAL_INTERVENTION if payload.is_critical_flag else ExecutionStatus.ELEVATED_RISK,
                summary=res["summary"],
                technical_details=res["details"],
                actionable_remediation=res["remediation"],
            ))
        return alerts


class HazardRatioSynthesizerAgent:
    """Specialized Sub-Agent 3: Protocol Conformance & Anomaly Triager."""
    def audit(self, payload: FrontierPayload) -> List[AgentTelemetryAlert]:
        alerts = []
        res = FrontierDomainEngine.audit_specification_conformance(payload.status_descriptor, payload.attributes)
        if res:
            alerts.append(AgentTelemetryAlert(
                alert_id=str(uuid.uuid4())[:8],
                origin_agent="HazardRatioSynthesizerAgent",
                status=ExecutionStatus.ELEVATED_RISK,
                summary=res["summary"],
                technical_details=res["details"],
                actionable_remediation=res["remediation"],
            ))
        return alerts


class FedCoxCoordinator:
    """Executive Coordinator & Air-Gapped Supervisory Intelligence."""
    def __init__(self):
        self.sub_1 = LocalGradientHessianAgent()
        self.sub_2 = CentralAggregatorAgent()
        self.sub_3 = HazardRatioSynthesizerAgent()
        self.execution_ledger: Dict[str, Dict[str, Any]] = {}

    def process(self, payload: FrontierPayload) -> Dict[str, Any]:
        # Validate all outbound fields; never suppress validation failures.
        from agents.base import PHIGuard
        for value in (payload.task_id, payload.target_identifier, payload.status_descriptor):
            PHIGuard.assert_no_phi(value)
        PHIGuard.assert_no_phi(json.dumps(payload.attributes, default=str))

        all_alerts: List[AgentTelemetryAlert] = []
        all_alerts.extend(self.sub_1.audit(payload))
        all_alerts.extend(self.sub_2.audit(payload))
        all_alerts.extend(self.sub_3.audit(payload))

        crit_count = sum(1 for a in all_alerts if a.status == ExecutionStatus.CRITICAL_INTERVENTION)
        warn_count = sum(1 for a in all_alerts if a.status == ExecutionStatus.ELEVATED_RISK)

        if crit_count > 0:
            status = ExecutionStatus.CRITICAL_INTERVENTION
        elif warn_count > 0:
            status = ExecutionStatus.ELEVATED_RISK
        else:
            status = ExecutionStatus.NOMINAL

        dossier = {
            "system": "federated-survival-cox-ph-agent",
            "domain": "Privacy-Preserving Federated Healthcare & FHE",
            "task_id": payload.task_id,
            "target_identifier": payload.target_identifier,
            "overall_status": status.value,
            "total_alerts": len(all_alerts),
            "critical_count": crit_count,
            "warning_count": warn_count,
            "alerts": [a.to_dict() for a in all_alerts],
            "standard_specification": "Distributed Survival Analysis Protocols",
            "consensus_summary": f"Consensus evaluation completed across 3 sub-agents with status [{status.value}].",
        }

        self.execution_ledger[payload.task_id] = dossier

        # Record audit entry
        _record_audit(
            actor="FedCoxCoordinator",
            event_type="TASK_EVALUATION_COMPLETED",
            details={
                "task_id": payload.task_id,
                "overall_status": status.value,
                "total_alerts": len(all_alerts),
            },
        )

        return dossier

    def query_supervisory_chat(self, query: str) -> str:
        q = query.strip().lower()
        if "status" in q or "ledger" in q:
            return f"FedCox-PH: Federated Stratified Cox Proportional Hazards Regression Agent currently managing {len(self.execution_ledger)} execution tasks in air-gapped memory."
        elif "standard" in q or "spec" in q:
            return "Active runtime operating strictly according to Distributed Survival Analysis Protocols specifications."
        else:
            return f"FedCox-PH: Federated Stratified Cox Proportional Hazards Regression Agent executive coordinator online. Zero-telemetry on-premises surveillance active."
