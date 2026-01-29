from __future__ import annotations

from pathlib import Path
import tempfile


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding=encoding, dir=str(path.parent)) as tf:
        tf.write(content)
        tmp = Path(tf.name)
    tmp.replace(path)


def ep_dir(root: Path, episode: int) -> Path:
    return root / "episodes" / f"ep{episode:04d}"
