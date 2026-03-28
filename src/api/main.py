from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import time
import os

from src.models.predictor import predictor
from src.utils.cache import memory_cache
from src.utils.audit_logger import get_recent_logs

app = FastAPI(
    title="Corporate Toxic Comment Detector API",
    description="Enterprise-grade Hybrid ML + GenAI Toxicity Evaluation API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS Middleware — allow React frontend (dev + production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InferenceRequest(BaseModel):
    comment: str

class InferenceResponse(BaseModel):
    comment: str
    masked_comment: str
    normalized_comment: str
    ml_score: float
    llm_label: str
    llm_confidence: float
    hybrid_score: float
    is_toxic: bool
    risk_level: str
    policy_violation: str
    llm_explanation: str
    cached: bool
    latency_ms: float

class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    original_text_masked: str
    ml_score: Optional[float]
    llm_confidence: Optional[float]
    hybrid_score: Optional[float]
    risk_level: Optional[str]
    policy_violation: Optional[str]

class HealthResponse(BaseModel):
    status: str
    ml_model: str
    llm_model: str
    cache_hits: int
    cache_misses: int
    uptime: str

_start_time = time.time()

# ═══════════════════════════════════════════
# API ROUTES — served under /api prefix
# (frontend Vite proxy strips /api in dev,
#  and in production we mount these at /api)
# ═══════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def detailed_health():
    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return HealthResponse(
        status="operational",
        ml_model="TF-IDF + LogisticRegression (88.6% accuracy)",
        llm_model="unitary/toxic-bert (95% F1)",
        cache_hits=memory_cache.hits,
        cache_misses=memory_cache.misses,
        uptime=f"{hours}h {minutes}m {seconds}s"
    )

@app.post("/api/predict", response_model=InferenceResponse)
@app.post("/predict", response_model=InferenceResponse, include_in_schema=False)
def predict_toxicity(request: InferenceRequest):
    start_time = time.time()
    text = request.comment.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Comment cannot be empty.")
    
    # 1. Check Enterprise Cache
    cached_result = memory_cache.get(text)
    if cached_result:
        latency_ms = (time.time() - start_time) * 1000
        return InferenceResponse(
            **cached_result, 
            cached=True, 
            latency_ms=round(latency_ms, 2)
        )
        
    # 2. Run Heavy Predictor Pipeline
    try:
        result = predictor.predict(text)
        
        # 3. Store in cache
        memory_cache.set(text, result)
        
        latency_ms = (time.time() - start_time) * 1000
        return InferenceResponse(
            **result, 
            cached=False, 
            latency_ms=round(latency_ms, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audit-logs", response_model=List[AuditLogEntry])
@app.get("/audit-logs", response_model=List[AuditLogEntry], include_in_schema=False)
def get_audit_logs(limit: int = 50):
    """Retrieve recent inference audit logs."""
    try:
        logs = get_recent_logs(limit)
        return [
            AuditLogEntry(
                id=log.id,
                timestamp=log.timestamp.isoformat() if log.timestamp else "",
                original_text_masked=log.original_text_masked or "",
                ml_score=log.ml_score,
                llm_confidence=log.llm_confidence,
                hybrid_score=log.hybrid_score,
                risk_level=log.risk_level,
                policy_violation=log.policy_violation,
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════
# STATIC FILE SERVING (Production)
# Serves the built React frontend from /static
# ═══════════════════════════════════════════
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static")
if os.path.isdir(STATIC_DIR):
    print(f"📦 Serving frontend from {os.path.abspath(STATIC_DIR)}")
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve React SPA — all non-API routes return index.html."""
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"status": "Enterprise API Operational", "docs": "/api/docs"}
