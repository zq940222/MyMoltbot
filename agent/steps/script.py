from __future__ import annotations

from agent.config import load_project
from agent.io import atomic_write, ep_dir
from agent.registry import StepContext, register

import yaml


def _load_yaml(path):
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _char_name(bible: dict, cid: str) -> str:
    for c in (bible.get("characters", []) or []):
        if c.get("id") == cid:
            return c.get("name") or cid
    return cid


@register("script")
def run_script(ctx: StepContext) -> None:
    """Generate a deterministic scene-based script scaffold."""

    project = load_project(ctx.root)
    ep = ep_dir(project.root, ctx.episode)

    out_path = ep / "script.md"
    if out_path.exists() and not ctx.force:
        return

    brief = _load_yaml(ep / "brief.yaml")
    bible = project.series_bible

    title = brief.get("title_working") or f"EP{ctx.episode:04d}"
    purpose = brief.get("purpose") or ""
    req = brief.get("required", {}) or {}
    cids = req.get("characters", []) or []

    names = {cid: _char_name(bible, cid) for cid in cids}

    scenes = [
        ("SC01", "外门院·清晨", "hook", [
            (names.get("C2", "反派"), "冷笑", "来，废柴，示范一下什么叫不配。"),
            (names.get("C1", "主角"), "压着怒", "我只求考核资格。"),
        ]),
        ("SC02", "管事处·白天", "setup", [
            ("管事", "敷衍", "名册上没你。"),
            (names.get("C1", "主角"), "克制", "我昨日的贡献——"),
        ]),
        ("SC03", "藏经阁外·夜", "escalation_1", [
            ("执事", "冷", "想学？先去后山废井，把遗失法器取回。"),
            (names.get("C2", "反派"), "假惺惺", "他只是想看看门规。"),
        ]),
        ("SC04", "后山废井口·夜", "mid_turn", [
            (names.get("C1", "主角"), "喘息", "……别掉下去。"),
            ("仙箓", "浮现", "以命换路，以弱破局。"),
        ]),
        ("SC05", "废井深处·夜", "escalation_2", [
            (names.get("C1", "主角"), "咬牙", "我不会按你们写好的结局走。"),
        ]),
        ("SC06", "外门院·深夜", "cliffhanger", [
            (names.get("C2", "反派"), "命令", "东西给我。"),
            (names.get("C1", "主角"), "第一次不退", "不。"),
        ]),
    ]

    lines = [f"# EP{ctx.episode:04d} 剧本：{title}\n\n"]
    if purpose:
        lines.append(f"**Purpose**：{purpose}\n\n")

    for sid, loc, beat, dialog in scenes:
        lines.append(f"## {sid} {loc}（{beat}）\n")
        lines.append("- 动作：按镜头表实现（近景为主、快切）。\n")
        for who, emo, text in dialog:
            lines.append(f"- {who}（{emo}）：{text}\n")
        lines.append("\n")

    atomic_write(out_path, "".join(lines))
