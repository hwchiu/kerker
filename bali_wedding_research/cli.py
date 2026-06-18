from __future__ import annotations

import argparse
from pathlib import Path

from .derive import write_derived_indexes
from .io import validate_workspace
from .paths import ensure_workspace_layout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bali_wedding_research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-workspace")
    init_parser.add_argument("--root", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", default=".")

    derived_parser = subparsers.add_parser("build-derived")
    derived_parser.add_argument("--root", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "init-workspace":
        created = ensure_workspace_layout(root)
        for path in created:
            print(path)
        return 0

    if args.command == "validate":
        counts = validate_workspace(root)
        print(
            f"validated venues={counts['venues']} "
            f"sources={counts['sources']} "
            f"photos={counts['photos']}"
        )
        return 0

    if args.command == "build-derived":
        outputs = write_derived_indexes(root)
        for path in outputs:
            print(path)
        return 0

    parser.error("unsupported command")
    return 2
