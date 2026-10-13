# Polypharmacy Deprescribing Agent

**Synthetic metric and rule-orchestration demonstration.** This repository contains several legacy Python interfaces that evaluate numeric thresholds, boolean flags, and status keywords. Despite their historical naming, **they do not ingest medication lists or implement AGS Beers 2023, STOPP/START, anticholinergic-burden scoring, interaction screening, or patient-specific deprescribing.** Do not use the outputs for clinical decisions.

## Browser demonstration

Open `web/index.html` locally to run the repository's three generic supervisor rules entirely in the browser. The page has no external network dependencies, servers, or accounts. Enter **synthetic data only**, review the deterministic alerts, and optionally download the result as JSON. The JavaScript mirrors the thresholds in `agents/workers.py`; no Python runtime is required for this small rule set.

GitHub Pages deployment is configured through `.github/workflows/pages.yml`. A public live URL should only be published here after the Pages deployment is confirmed operational.

## Python interfaces

Requires Python 3.9+; Python 3.10–3.12 are exercised in CI. From a source checkout:

```bash
python -m pip install -e '.[api,test]'
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py audit --task-id DEMO-001 --primary 28 --secondary 14
python cli.py batch --input sample.csv --output results.csv
python cli.py serve --host 127.0.0.1 --port 8000
```

The root `cli.py` runs the Pydantic-based supervisor and signs **in-memory** audit metadata using HMAC-SHA256. Its API supports `GET /health`, `GET /metrics` (JSON, not Prometheus text), `POST /api/audit`, and `POST /api/chat`. The `GET /api/audit/logs` endpoint is disabled unless `AUDIT_LOG_READ_TOKEN` is configured, in which case clients must provide `Authorization: Bearer <token>`.

Separate legacy interfaces remain available through `python deprescribe_mind.py` and `python -m polypharmacy_deprescribing_agent.cli`. These implement different synthetic thresholds and output schemas. The installed CLI entry point `polypharmacy-deprescribing-engine` invokes the latter. Do not interchange their input formats.

## Docker

Generate and export a strong `AUDIT_SECRET_KEY` in the host environment, then run:

```bash
docker compose up --build
```

The API is exposed on port 8000. Keep it behind an authentication layer and appropriate network restrictions if accessible beyond the local machine. The repository's example server is **not** a production PHI platform.

## Tests and security limitations

```bash
python -m pytest -v
python -m compileall -q agents polypharmacy_deprescribing_agent
```

CI runs the Python test suite and checks browser JavaScript syntax. Regression tests cover HMAC metadata integrity, non-finite metric rejection, CSV boolean parsing, basic identifier-pattern blocking, and audit-log access control.

The identifier guard uses **heuristic regular expressions**, not validated de-identification or HIPAA Safe Harbor certification. Do not submit real patient identifiers. Audit logs are **process-local**, not persistent or independently anchored; signatures protect recorded metadata but cannot prove the correctness of clinical decisions. Other described features such as autonomous learning, external model providers, and medication-specific rules are not integrated into the main supervisor workflow.

No clinical validity, medication safety, regulatory compliance, or real-world deprescribing efficacy is claimed.

## Technology and license

Python, Pydantic v2, optional FastAPI/Uvicorn, HTML/CSS/JavaScript, GitHub Actions, Docker. Browser demo works in modern desktop and mobile browsers with JavaScript enabled. Distributed under the [MIT License](LICENSE).
