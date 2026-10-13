"""
Command Line Interface for Federated Survival Cox Ph Agent.
"""
import argparse
import csv
import json
import sys
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger
from fed_cox_ph.cox import CoxSite, fit_federated_cox

supervisor = SystemSupervisor(model_provider="mock")


def parse_csv_bool(value: object) -> bool:
    """Parse a boolean column without treating 'False' as truthy."""
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off", ""}:
        return False
    raise ValueError(f"Invalid is_critical_flag: {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="federated-survival-cox-ph-agent", description="Federated Survival Cox Ph Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # In-process multi-site Cox model demonstration (not a network federation).
    p_cox = subparsers.add_parser("fit-cox", help="Fit Breslow Cox PH from local site CSV files")
    p_cox.add_argument("--site", action="append", required=True, help="Per-site CSV with time,event,cov_* columns; repeat per site")
    p_cox.add_argument("--ridge", type=float, default=0.0, help="Optional L2 penalty")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  FEDERATED SURVIVAL COX PH AGENT")
        print(f"  Domain: Privacy-Preserving Federated Healthcare & FHE | Standard: HIPAA Safe Harbor §164.514 / Google SecAgg Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Federated Survival Cox Ph Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = list(dict.fromkeys(fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]))
        out_rows = []
        for r in rows:
            payload = SystemTaskPayload(
                task_id=r.get("task_id", "TASK-01"),
                target_identifier=r.get("target_identifier", "TARGET-01"),
                primary_metric=float(r.get("primary_metric", 15.0)),
                secondary_metric=float(r.get("secondary_metric", 5.0)),
                status_descriptor=r.get("status_descriptor", "NOMINAL"),
                is_critical_flag=parse_csv_bool(r.get("is_critical_flag", False)),
            )
            dossier = supervisor.process_task(payload)
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "fit-cox":
        sites = []
        expected_covariates = None
        for site_path in args.site:
            with open(site_path, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                covariates = [name for name in headers if name.startswith("cov_")]
                if not {"time", "event"}.issubset(headers) or not covariates:
                    raise ValueError(f"{site_path}: require time, event and cov_* columns")
                if expected_covariates is None:
                    expected_covariates = covariates
                elif covariates != expected_covariates:
                    raise ValueError("all sites must have identical ordered cov_* columns")
                records = []
                for row in reader:
                    records.append({
                        "time": row["time"],
                        "event": int(row["event"]),
                        "covariates": [row[name] for name in covariates],
                        "stratum": row.get("stratum") or "all",
                    })
                sites.append(CoxSite(records))
        result = fit_federated_cox(sites, ridge=args.ridge)
        output = result.to_dict()
        output["covariates"] = expected_covariates
        print(json.dumps(output, indent=2))
        return 0 if result.converged else 2

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Federated Survival Cox Ph Agent API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
