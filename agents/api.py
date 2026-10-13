"""
FastAPI REST API Server for Polypharmacy Deprescribing Agent.
"""
from typing import Dict, Any, List
import hmac
import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Polypharmacy Deprescribing Agent API",
    description="Synthetic metric threshold demonstration; not a medication review or clinical decision support system.",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.exception_handler(SecurityException)
async def handle_identifier_violation(request, exc):
    return JSONResponse(status_code=400, content={
        "detail": "Potential identifier detected. Use synthetic, de-identified data."
    })


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "polypharmacy-deprescribing-agent", "domain": "Clinical Pharmacology & Pharmacogenomics", "standard": "CPIC Level A / FDA Guidance / ISMP Safety Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(authorization: str = Header(default="")):
    # An explicit, separate administrative token is required to expose process audit metadata.
    token = os.getenv("AUDIT_LOG_READ_TOKEN")
    if not token:
        raise HTTPException(status_code=404, detail="Audit log endpoint is disabled")
    expected = "Bearer " + token
    if not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
