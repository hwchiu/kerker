from __future__ import annotations

import argparse
from pathlib import Path

from .derive import write_derived_indexes
from .io import load_json_file, validate_workspace, write_json_file
from .notes import write_all_venue_notes
from .paths import ensure_workspace_layout, workspace_paths
from .seed_registry import merge_seed_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bali_wedding_research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-workspace")
    init_parser.add_argument("--root", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", default=".")

    derived_parser = subparsers.add_parser("build-derived")
    derived_parser.add_argument("--root", default=".")

    notes_parser = subparsers.add_parser("build-notes")
    notes_parser.add_argument("--root", default=".")

    seed_parser = subparsers.add_parser("merge-seeds")
    seed_parser.add_argument("--root", default=".")
    seed_parser.add_argument("--input", action="append", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        if isinstance(error.code, int):
            return error.code
        return 1
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

    if args.command == "build-notes":
        outputs = write_all_venue_notes(root)
        for path in outputs:
            print(path)
        return 0

    if args.command == "merge-seeds":
        paths = workspace_paths(root)
        raw_entries: list[dict[str, object]] = []
        for input_path in args.input:
            payload = load_json_file(Path(input_path))
            if isinstance(payload, list):
                raw_entries.extend(payload)
            else:
                raw_entries.append(payload)
        merged = merge_seed_registry(raw_entries)
        output_path = paths["seeds"] / "venue-seeds.json"
        write_json_file(output_path, merged)
        print(output_path)
        return 0

    parser.error("unsupported command")
    return 2
