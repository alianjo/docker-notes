"""A small FastAPI + PostgreSQL example for learning Docker Compose."""

from contextlib import asynccontextmanager
import os
from typing import Annotated

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator


DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "docker_notes")
DB_USER = os.getenv("DB_USER", "docker_notes")
DB_PASSWORD = os.getenv("DB_PASSWORD")


if not DB_PASSWORD:
    raise RuntimeError(
        "DB_PASSWORD is required. Copy .env.example to .env and set a local password."
    )


def connect_db():
    """Open a PostgreSQL connection using discrete, safely passed parameters."""
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=3,
        row_factory=dict_row,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the example table when the API starts."""
    with connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id BIGSERIAL PRIMARY KEY,
                content TEXT NOT NULL CHECK (length(trim(content)) > 0),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    yield


app = FastAPI(
    title="Docker Notes API + PostgreSQL",
    description="A practical API/database example managed with Docker Compose.",
    version="1.0.0",
    lifespan=lifespan,
)


class NoteCreate(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=1000)]

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


@app.get("/")
def root():
    return {
        "message": "Docker Notes API with PostgreSQL is running.",
        "docs": "/docs",
        "health": "/health/ready",
    }


@app.get("/health/live")
def liveness():
    """Report that the API process can answer requests; no database query."""
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    """Report readiness only if PostgreSQL can answer a simple query."""
    try:
        with connect_db() as connection:
            connection.execute("SELECT 1")
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from exc
    return {"status": "ok", "database": "ok"}


@app.get("/api/v1/notes")
def list_notes():
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return {"items": rows, "count": len(rows)}


@app.post("/api/v1/notes", status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate):
    try:
        with connect_db() as connection:
            row = connection.execute(
                """
                INSERT INTO notes (content)
                VALUES (%s)
                RETURNING id, content, created_at
                """,
                (payload.content,),
            ).fetchone()
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not write to the database",
        ) from exc
    return row
