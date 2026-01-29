from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.runner import run_steps

ROOT = Path(__file__).resolve().parents[2]


def safe_path(p: str) -> Path:
    path = (ROOT / p).resolve()
    if not str(path).startswith(str(ROOT.resolve())):
        raise ValueError("Path escapes project root")
    return path


app = FastAPI(title="AI Short Drama MVP")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    index_path = ROOT / "server" / "static" / "index.html"
    return index_path.read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=str(ROOT / "server" / "static")), name="static")


@app.get("/api/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "root": str(ROOT),
        "env": {
            "CODESPACE_NAME": os.environ.get("CODESPACE_NAME"),
            "GITHUB_REPOSITORY": os.environ.get("GITHUB_REPOSITORY"),
        },
    }


@app.get("/api/episodes")
def list_episodes() -> list[dict[str, Any]]:
    eps_dir = ROOT / "episodes"
    if not eps_dir.exists():
        return []
    out = []
    for p in sorted(eps_dir.glob("ep[0-9][0-9][0-9][0-9]")):
        out.append({"id": p.name, "path": str(p.relative_to(ROOT))})
    return out


class GenerateReq(BaseModel):
    steps: list[str] = ["outline", "script", "shotlist", "package"]
    force: bool = False


@app.post("/api/episodes/{episode}/generate")
def generate_episode(episode: int, req: GenerateReq) -> dict[str, Any]:
    try:
        run_steps(root=str(ROOT), episode=episode, steps=req.steps, force=req.force)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True, "episode": episode, "steps": req.steps, "force": req.force}


@app.get("/api/episodes/{episode}/files")
def episode_files(episode: int) -> list[str]:
    ep_dir = ROOT / "episodes" / f"ep{episode:04d}"
    if not ep_dir.exists():
        raise HTTPException(status_code=404, detail="episode not found")
    files = []
    for p in ep_dir.rglob("*"):
        if p.is_file():
            files.append(str(p.relative_to(ROOT)))
    return sorted(files)


@app.get("/api/file")
def read_file(path: str) -> PlainTextResponse:
    try:
        p = safe_path(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    # Basic safety: don't serve .git
    if ".git" in p.parts:
        raise HTTPException(status_code=403, detail="forbidden")
    text = p.read_text(encoding="utf-8", errors="replace")
    return PlainTextResponse(text)


@app.get("/api/shotlist/summary")
def shotlist_summary(episode: int) -> dict[str, Any]:
    import csv

    shotlist = ROOT / "episodes" / f"ep{episode:04d}" / "shotlist.csv"
    if not shotlist.exists():
        raise HTTPException(status_code=404, detail="shotlist not found")
    with shotlist.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    video = sum(1 for r in rows if r.get("output_type") == "video")
    total_sec = sum(int(float(r.get("duration_sec") or 0)) for r in rows)
    scenes = len({r.get("scene_id") for r in rows if r.get("scene_id")})
    return {"episode": episode, "shots": total, "video": video, "total_sec": total_sec, "scenes": scenes}
