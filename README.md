# Polypharmacy Deprescribing Agent

> **Domain:** Clinical Pharmacology & Precision Pharmacotherapy  
> **Reference Guidelines & Standards:** `CPIC Guidelines & FDA Table of Pharmacogenomic Biomarkers`

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

**Polypharmacy Deprescribing Agent** is an advanced analytical and computational platform implementing AGS Beers 2023 Criteria & Anticholinergic Cognitive Burden Agent.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`BeersCriteriaMatcherAgent`**: Specialized Sub-Agent 1 for polypharmacy-deprescribing-agent
- **`AnticholinergicBurdenCalculatorAgent`**: Specialized Sub-Agent 2 for polypharmacy-deprescribing-agent
- **`DeprescribingPrioritizerAgent`**: Specialized Sub-Agent 3 for polypharmacy-deprescribing-agent

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --task-id <value> --target <value> --primary <value> --secondary <value>
```

### Parameter Reference
| Parameter | Command | Description | Default |
|:----------|:--------|:------------|:--------|
| `--task-id` | `audit` | Unique task/case identifier | `TASK-2026-001` |
| `--target` | `audit` | Target entity or patient key identifier | `KEY-TARGET-01` |
| `--primary` | `audit` | Primary domain measurement or score (float) | `28.5` |
| `--secondary` | `audit` | Secondary kinetic or confidence score (float) | `14.2` |
| `--critical` | `audit` | Flag for emergency escalation (boolean) | `False` |
| `--status` | `audit` | Status code or phenotype descriptor | `DISCORDANT` |
| `-i, --input` | `batch` | Path to input CSV file for batch processing | *required* |
| `-o, --output` | `batch` | Path to output CSV file for results | `results.csv` |
| `--host` | `serve` | Host address for the REST server | `127.0.0.1` |
| `--port` | `serve` | Port number for the REST server | `8000` |

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🔧 Configuration

The audit system requires an `AUDIT_SECRET_KEY` environment variable for HMAC-SHA256 signing:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-audit-key"

# Windows
set AUDIT_SECRET_KEY=your-secure-audit-key
```

The CLI sets a default key automatically if none is provided. For production deployments, always set a strong secret.

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t polypharmacy-deprescribing-agent .
docker run -p 8000:8000 polypharmacy-deprescribing-agent
```
