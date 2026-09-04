# Federated Survival Cox PH Agent

> **Domain:** Privacy-Preserving Healthcare & Federated Computing  
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Federated Survival Cox PH Agent** is an advanced analytical and computational platform implementing Decentralized Newton-Raphson stratified Cox proportional hazards regression agent.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Federated Stratified Cox PH Regression**: Distributed Newton-Raphson optimization across siloed healthcare centers.

---

## 💻 CLI Quickstart & Usage

### Installation
```bash
pip install -e .
```

### Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### Start REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Argument | Description | Default |
|:---------|:------------|:--------|
| `--task-id` | Unique task/case identifier | `TASK-2026-001` |
| `--target` | Entity, patient key, or target | `KEY-TARGET-01` |
| `--primary` | Primary domain measurement | `28.5` |
| `--secondary` | Secondary kinetic/confidence score | `14.2` |
| `--critical` | Emergency escalation flag | `False` |
| `--status` | Status code or phenotype descriptor | `DISCORDANT` |

### Input Data Schema (CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task/case identifier | Required |
| `target_identifier` | Entity or target key | Required |
| `primary_metric` | Primary domain measurement | Required |
| `secondary_metric` | Secondary kinetic/confidence score | Required |
| `is_critical_flag` | Emergency escalation flag | Required |
| `status_descriptor` | Status code or phenotype descriptor | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable in production:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

### Docker
```bash
docker build -t federated-survival-cox-ph-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key federated-survival-cox-ph-agent
```

### Docker Compose
```bash
# Create .env file with your secure key
echo "AUDIT_SECRET_KEY=your-secure-key" > .env

# Start the service
docker compose up -d
```

---

## 📁 Project Structure

```
federated-survival-cox-ph-agent/
├── agents/                  # Core agent modules (supervisor, workers, PHI guard)
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, HMAC audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Master orchestrator
│   ├── workers.py          # Specialized domain workers
│   └── ...
├── fed_cox_ph/             # Federated Cox PH regression engine
│   ├── agents.py           # Sub-agents and coordinator
│   ├── engine.py           # Core algorithmic engine
│   ├── models.py           # Data models
│   ├── cli.py              # CLI interface
│   └── server.py           # FastAPI server factory
├── tests/                  # Pytest test suite
├── web/                    # Operations console (HTML/JS)
├── cli.py                  # Main CLI entry point
├── simulator.py            # High-throughput simulation
├── enrichment.py           # Additional domain features
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-container orchestration
└── pyproject.toml          # Project metadata and dependencies
```
