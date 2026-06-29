from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.db import memory as mem_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
from src.db.schema import migrate
from src.embeddings.provider import get_provider
from src.studio.graph import build_graph

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="specify studio", docs_url=None, redoc_url=None)


def _load_embeddings(conn) -> dict[int, list[float]]:
    rows = conn.execute("SELECT memory_id, embedding FROM vec_memories").fetchall()
    import json

    result = {}
    for row in rows:
        try:
            result[row[0]] = json.loads(row[1])
        except Exception:
            pass
    return result


def _get_conn():
    from src.core.project import get_project_paths

    paths = get_project_paths()
    conn = get_connection(paths.db_path, check_same_thread=False)
    migrate(conn)
    return conn


@app.get("/api/graph")
def get_graph():
    conn = _get_conn()
    try:
        embeddings = _load_embeddings(conn)
        return build_graph(conn, embeddings=embeddings)
    finally:
        conn.close()


@app.get("/api/memories/{memory_id}")
def get_memory(memory_id: int):
    conn = _get_conn()
    try:
        m = mem_db.get(conn, memory_id)
        if m is None:
            raise HTTPException(status_code=404, detail="not found")
        return {
            "id": m.id,
            "type": m.type,
            "scope": m.scope,
            "content": m.content,
            "source": m.source,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
    finally:
        conn.close()


class MemoryUpdate(BaseModel):
    content: str


@app.put("/api/memories/{memory_id}")
def update_memory(memory_id: int, body: MemoryUpdate):
    conn = _get_conn()
    try:
        m = mem_db.get(conn, memory_id)
        if m is None:
            raise HTTPException(status_code=404, detail="not found")
        mem_db.update(conn, memory_id, body.content)
        provider = get_provider(warn=False)
        if provider.available():
            embedding = provider.embed(body.content)
            if embedding:
                vec_db.upsert_embedding(conn, memory_id, embedding)
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/memories/{memory_id}")
def delete_memory(memory_id: int):
    conn = _get_conn()
    try:
        m = mem_db.get(conn, memory_id)
        if m is None:
            raise HTTPException(status_code=404, detail="not found")
        vec_db.delete_embedding(conn, memory_id)
        mem_db.delete(conn, memory_id)
        return {"ok": True}
    finally:
        conn.close()


app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
