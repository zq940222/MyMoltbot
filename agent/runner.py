from __future__ import annotations

import argparse

from agent.registry import StepContext, get_step, list_steps

# Import steps to populate registry
import agent.steps  # noqa: F401


def run_steps(*, root: str, episode: int, steps: list[str], force: bool = False) -> None:
    ctx = StepContext(root=root, episode=episode, steps=steps, force=force)
    for name in steps:
        fn = get_step(name)
        fn(ctx)


def main() -> None:
    p = argparse.ArgumentParser(prog="drama-agent")
    p.add_argument("command", choices=["run", "steps"], help="Run pipeline or list steps")
    p.add_argument("--root", default=".")
    p.add_argument("--episode", type=int, default=1)
    p.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    p.add_argument(
        "--steps",
        default="outline,script,shotlist,package",
        help="Comma-separated step names. Use 'steps' command to list available.",
    )

    args = p.parse_args()

    if args.command == "steps":
        for s in list_steps():
            print(s)
        return

    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    run_steps(root=args.root, episode=args.episode, steps=steps, force=args.force)
    for name in steps:
        print(f"OK: {name}")


if __name__ == "__main__":
    main()
