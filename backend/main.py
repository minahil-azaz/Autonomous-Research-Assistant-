"""
Autonomous Research Assistant — FastAPI Backend
Entry point. Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.stream import router as stream_router
from api.export import router as export_router

app = FastAPI(
    title="Autonomous Research Assistant",
    description="Agentic research system with iterative search, reflection, and PDF export.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router, prefix="/api")
app.include_router(export_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
