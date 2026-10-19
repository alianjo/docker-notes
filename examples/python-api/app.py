"""Small FastAPI application used by the Docker Notes handbook."""

import os

from fastapi import FastAPI, Query

APP_NAME = os.getenv("APP_NAME", "Docker Notes API").strip() or "Docker Notes API"
APP_VERSION = "1.0.0"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A small API for learning how to containerize a Python service.",
)


@app.get("/", tags=["general"])
def root() -> dict[str, str]:
    """Return a short API overview."""
    return {
        "message": "Docker Notes Python API is running.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Provide a lightweight process-level health endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/info", tags=["general"])
def info() -> dict[str, str]:
    """Return public application metadata, not environment contents."""
    return {"name": app.title, "version": app.version}


@app.get("/api/v1/greet", tags=["general"])
def greet(
    name: str = Query(default="developer", min_length=1, max_length=80),
) -> dict[str, str]:
    """Return a greeting to demonstrate query parameters and JSON output."""
    cleaned_name = name.strip()
    if not cleaned_name:
        cleaned_name = "developer"
    return {"message": f"Hello, {cleaned_name}!"}
