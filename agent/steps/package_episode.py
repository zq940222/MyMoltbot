from __future__ import annotations

import csv
import json
from pathlib import Path

from agent.config import load_project
from agent.io import ep_dir
from agent.registry import StepContext, register


def _read_shotlist(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@register("package")
def run_package(ctx: StepContext) -> None:
    """Create a render-ready episode folder (no ComfyUI calls)."""

    project = load_project(ctx.root)
    ep = ep_dir(project.root, ctx.episode)

    shotlist_path = ep / "shotlist.csv"
    if not shotlist_path.exists():
        raise FileNotFoundError(f"Missing shotlist: {shotlist_path}")

    shots = _read_shotlist(shotlist_path)

    # Ensure standard dirs
    (ep / "prompts").mkdir(parents=True, exist_ok=True)
    (ep / "storyboard").mkdir(parents=True, exist_ok=True)
    (ep / "clips").mkdir(parents=True, exist_ok=True)
    (ep / "assets").mkdir(parents=True, exist_ok=True)
    (ep / "delivery").mkdir(parents=True, exist_ok=True)

    def to_task(s: dict) -> dict:
        return {
            "shot_id": s.get("shot_id"),
            "episode": int(s.get("episode") or ctx.episode),
            "scene_id": s.get("scene_id"),
            "beat": s.get("beat"),
            "duration_sec": int(float(s.get("duration_sec") or 0)),
            "output_type": s.get("output_type"),
            "priority": s.get("priority"),
            "output_path": s.get("output_path"),
            "seed": int(s.get("seed")) if (s.get("seed") or "").strip() else None,
            "reference_pack": [p.strip() for p in (s.get("reference_pack") or "").split(";") if p.strip()],
            "prompt": (s.get("video_prompt") if s.get("output_type") == "video" else s.get("storyboard_prompt"))
            or "",
            "negative_prompt": s.get("negative_prompt") or "",
            "meta": {
                "location": s.get("location_name"),
                "characters": s.get("characters"),
                "wardrobe": s.get("wardrobe"),
                "props": s.get("props"),
                "continuity_notes": s.get("continuity_notes"),
            },
        }

    storyboard_tasks = [to_task(s) for s in shots if s.get("output_type") != "video"]
    video_tasks = [to_task(s) for s in shots if s.get("output_type") == "video"]

    def write_jsonl(path: Path, items: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

    write_jsonl(ep / "prompts" / "storyboard_tasks.jsonl", storyboard_tasks)
    write_jsonl(ep / "prompts" / "video_tasks.jsonl", video_tasks)

    (ep / "delivery" / "RENDER_PLAN.md").write_text(
        (
            f"# EP{ctx.episode:04d} 渲染计划（ComfyUI 预留）\n\n"
            f"- storyboard: {len(storyboard_tasks)} 帧（输出到 episodes/ep{ctx.episode:04d}/storyboard/）\n"
            f"- video clips: {len(video_tasks)} 条（输出到 episodes/ep{ctx.episode:04d}/clips/）\n\n"
            "## 输入文件\n"
            f"- shotlist: episodes/ep{ctx.episode:04d}/shotlist.csv\n"
            f"- storyboard tasks: episodes/ep{ctx.episode:04d}/prompts/storyboard_tasks.jsonl\n"
            f"- video tasks: episodes/ep{ctx.episode:04d}/prompts/video_tasks.jsonl\n"
        ),
        encoding="utf-8",
    )

    checklist = ep / "delivery" / "DELIVERY_CHECKLIST.md"
    checklist.write_text(
        "# 交付检查清单（不含渲染）\n\n"
        "## 文本资产\n"
        "- [x] brief.yaml\n- [x] outline.md\n- [x] script.md\n- [x] shotlist.csv\n\n"
        "## 渲染输入（ComfyUI预留）\n"
        "- [x] prompts/storyboard_tasks.jsonl\n- [x] prompts/video_tasks.jsonl\n- [x] delivery/RENDER_PLAN.md\n\n"
        "## 待渲染输出（目标路径）\n"
        "- [ ] storyboard/*.png\n- [ ] clips/*.mp4\n",
        encoding="utf-8",
    )
