from __future__ import annotations

from agent.config import load_project
from agent.io import atomic_write, ep_dir
from agent.registry import StepContext, register

import yaml


def _load_yaml(path):
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@register("outline")
def run_outline(ctx: StepContext) -> None:
    """Generate a deterministic episode outline from series bible + episode brief."""

    project = load_project(ctx.root)
    ep = ep_dir(project.root, ctx.episode)

    out_path = ep / "outline.md"
    if out_path.exists() and not ctx.force:
        return

    brief = _load_yaml(ep / "brief.yaml")
    bible = project.series_bible

    beats = (bible.get("format", {}) or {}).get("episode_beats", []) or []
    title = brief.get("title_working") or f"EP{ctx.episode:04d}"
    purpose = brief.get("purpose") or ""
    req = brief.get("required", {}) or {}

    chars = req.get("characters", []) or []
    locs = req.get("locations", []) or []
    plot_points = (req.get("plot_points", []) or [])

    def beat_section(b):
        name = b.get("beat", "")
        minutes = b.get("minutes", "")
        goal = b.get("goal", "")
        bullets = [
            f"- 当集目标推进：{purpose or '推进主线并制造代价'}",
            f"- 必须覆盖：{'; '.join(plot_points) if plot_points else '（待补充）'}",
            f"- 角色：{', '.join(chars) if chars else '（待补充）'}；地点：{', '.join(locs) if locs else '（待补充）'}",
        ]
        return f"## {name} ({minutes})\n- 目标：{goal}\n" + "\n".join(bullets) + "\n"

    content = [f"# EP{ctx.episode:04d} 大纲：{title}\n", f"**Purpose**：{purpose}\n" if purpose else "", "\n## 必要元素\n"]
    if chars:
        content.append(f"- 角色：{', '.join(chars)}\n")
    if locs:
        content.append(f"- 地点：{', '.join(locs)}\n")
    if plot_points:
        content.append("- 关键点：\n" + "\n".join([f"  - {p}" for p in plot_points]) + "\n")

    content.append("\n## 结构节拍\n")
    if beats:
        for b in beats:
            content.append(beat_section(b) + "\n")
    else:
        content.append("- （未在 specs/series_bible.yaml 中找到 episode_beats）\n")

    atomic_write(out_path, "".join(content))
