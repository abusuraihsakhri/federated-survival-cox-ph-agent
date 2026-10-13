# Federated Survival Cox PH Agent

### [Open the Live Application →](https://abusuraihsakhri.github.io/federated-survival-cox-ph-agent/)

A Python research prototype containing two distinct tools: an **experimental stratified Cox proportional hazards estimator** based on site-aggregated risk-set statistics, and a **deterministic rule-based task auditor** accessible through CLI, REST API, or a static browser interface.

**Scope:** The estimator uses Breslow handling of tied events and damped Newton–Raphson updates. It simulates multiple sites within one Python process; it does **not** implement a distributed network protocol, secure aggregation, homomorphic encryption, differential privacy, variance estimation, or proportional-hazards diagnostics. The rule-based task audit is **not** a Cox model and its thresholds are illustrative rather than validated clinical cutoffs.

## Run the browser demonstration

Open `web/index.html` in a browser, or serve the repository locally using the instructions below. The standalone browser application performs only the rule-based audit and works without a backend.

The GitHub Pages publication workflow deploys `web/` on changes to `master` and performs HTTPS smoke tests against the published HTML and JavaScript.

## Install and run

Requires Python 3.10 or later.

```bash
python -m pip install -e ".[server,test]"
python -m pytest -q
federated-survival-cox-ph-agent audit --task-id DEMO-01 --target KEY-01 --primary 28.5 --secondary 14.2 --status DISCORDANT
federated-survival-cox-ph-agent batch -i sample.csv -o results.csv
federated-survival-cox-ph-agent verify-audit
federated-survival-cox-ph-agent serve --host 127.0.0.1 --port 8000
```

The server offers `/` (browser console), `/health`, `/metrics`, `/api/audit`, `/api/chat`, and `/api/audit/logs`. The CLI also exposes a compatibility entry point `fed-cox-ph-legacy` for the alternate auditor.

### Experimental Cox model

```bash
federated-survival-cox-ph-agent fit-cox \
  --site sample_cox_site_a.csv \
  --site sample_cox_site_b.csv
```

Each site CSV must have `time` (nonnegative follow-up time), `event` (0/1), and one or more numeric `cov_*` columns in the **same order** across sites. An optional `stratum` column specifies a separate baseline hazard. Each `--site` file represents one simulated site. An optional `--ridge 0.1` applies L2 penalization; coefficients and hazard ratios are returned as JSON, including convergence status. Invalid, nonfinite, and unidentifiable models are rejected where detectable.

All site files are read on the same host, and individual observations remain in the site objects during fitting. Site-level event schedules, risk-score maxima, and first/second risk moments are exposed to the coordinator. **These aggregates may reveal sensitive information**, particularly with small risk sets. Do not use identifiable patient data or interpret the implementation as a privacy-preserving distributed deployment.

The model has numerical regression tests comparing its results to a separately evaluated pooled Breslow partial likelihood. Additional validation, uncertainty estimates, PH-assumption checks, federated transport, and disclosure controls are required before research production use.

## Auditor

The audit workflow evaluates arbitrary numeric metrics using predefined illustration thresholds (primary `>25`, secondary `>12` for the main supervisor), a critical flag, and anomaly keywords. It returns a structured assessment; the labels and remediation statements are *not clinical guidance*. CSV batch fields are `task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag`. The boolean column accepts `true/false`, `1/0`, and `yes/no` (case-insensitive).

In the browser, computation stays within the page and JSON reports can be downloaded. No browser-side HMAC audit signatures or invented API fallbacks are produced.

## Security and privacy limitations

- Text-pattern checks reject some common identifiers but cannot establish de-identification, HIPAA compliance, or comprehensive PHI detection. **Use synthetic, non-sensitive inputs.**
- Audit entries are HMAC-SHA256 chained and verification recomputes every signature; entries remain in memory and are lost on restart. Set a strong `AUDIT_SECRET_KEY` to use a stable signing key. Without it, the program generates a random process-local signing key.
- The REST server has **no user authentication**. Bind to a local interface or protect it behind an authenticated gateway. The example Docker Compose configuration binds port 8000 to loopback.
- Other modules under `enrichment.py` are rule-based status prototypes, **not** implementations of secure multiparty computation, differential privacy, formal Rényi accounting, or Byzantine-resistant inference.
- The mock language-model adapter returns deterministic placeholder responses; it does not contact hosted models or perform clinical reasoning.

## Container

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose up --build
```

The container runs as a non-root user. For manual Docker invocation, bind to `127.0.0.1:8000:8000` and pass a secure signing key via an environment variable.

## Development

Run `python -m pytest -q`, `node --check web/app.js`, and `node --test web/app.test.cjs`. GitHub Actions tests Python 3.10–3.12 and the browser evaluation logic. The runtime uses Pydantic 2; FastAPI and Uvicorn are optional server dependencies. The browser requires modern JavaScript support and works on desktop or mobile.

## License

MIT — see [LICENSE](LICENSE).
