from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class ProjectConfig:
    root: Path
    series_bible: dict
    platform: dict
    budget: dict


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_project(root: str | Path = Path(".")) -> ProjectConfig:
    root = Path(root)
    series_bible = _load_yaml(root / "specs" / "series_bible.yaml")
    platform = _load_yaml(root / "specs" / "platform" / "douyin.yaml")
    budget = _load_yaml(root / "specs" / "budget.yaml")
    return ProjectConfig(root=root, series_bible=series_bible, platform=platform, budget=budget)
