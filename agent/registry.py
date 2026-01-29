from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class StepContext:
    root: str
    episode: int
    steps: List[str]
    force: bool = False


StepFn = Callable[[StepContext], None]


_REGISTRY: Dict[str, StepFn] = {}


def register(name: str):
    def deco(fn: StepFn) -> StepFn:
        _REGISTRY[name] = fn
        return fn

    return deco


def get_step(name: str) -> StepFn:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown step: {name}. Available: {', '.join(sorted(_REGISTRY))}")
    return _REGISTRY[name]


def list_steps() -> List[str]:
    return sorted(_REGISTRY)
