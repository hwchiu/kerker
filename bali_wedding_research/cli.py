from __future__ import annotations

import argparse
from pathlib import Path

from .derive import write_derived_indexes
from .destinations import destination_ids, get_destination_config
from .io import load_json_file, validate_workspace, write_json_file
from .notes import write_all_venue_notes
from .paths import ensure_workspace_layout, workspace_paths
from .photo_assets import write_photo_assets
from .seed_registry import merge_seed_registry
from .site import serve_site, write_pages_site, write_static_site


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bali_wedding_research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-workspace")
    init_parser.add_argument("--root", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", default=".")
    validate_parser.add_argument("--destination", default="bali")

    derived_parser = subparsers.add_parser("build-derived")
    derived_parser.add_argument("--root", default=".")
    derived_parser.add_argument("--destination", default="bali")

    notes_parser = subparsers.add_parser("build-notes")
    notes_parser.add_argument("--root", default=".")

    photo_assets_parser = subparsers.add_parser("build-photo-assets")
    photo_assets_parser.add_argument("--root", default=".")
    photo_assets_parser.add_argument("--max-images-per-photo", type=int, default=6)
    photo_assets_parser.add_argument("--destination", default="bali")

    site_parser = subparsers.add_parser("build-site")
    site_parser.add_argument("--root", default=".")
    site_parser.add_argument("--output", default="site")
    site_parser.add_argument("--destination", default="bali")

    pages_parser = subparsers.add_parser("build-pages-site")
    pages_parser.add_argument("--root", default=".")

    serve_parser = subparsers.add_parser("serve-site")
    serve_parser.add_argument("--root", default=".")
    serve_parser.add_argument("--output", default="site")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)

    seed_parser = subparsers.add_parser("merge-seeds")
    seed_parser.add_argument("--root", default=".")
    seed_parser.add_argument("--input", action="append", required=True)

    return parser


def _selected_destinations(value: str) -> list[str]:
    if value == "all":
        return destination_ids()
    get_destination_config(value)
    return [value]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        if isinstance(error.code, int):
            return error.code
        return 1
    root = Path(args.root)
    output_dir = root / args.output if hasattr(args, "output") else None

    if args.command == "init-workspace":
        created = ensure_workspace_layout(root)
        for path in created:
            print(path)
        return 0

    if args.command == "validate":
        for destination_id in _selected_destinations(args.destination):
            counts = validate_workspace(root, destination_id)
            if args.destination == "bali":
                print(
                    f"validated venues={counts['venues']} "
                    f"sources={counts['sources']} "
                    f"photos={counts['photos']}"
                )
            else:
                print(
                    f"validated destination={destination_id} "
                    f"venues={counts['venues']} "
                    f"sources={counts['sources']} "
                    f"photos={counts['photos']}"
                )
        return 0

    if args.command == "build-derived":
        for destination_id in _selected_destinations(args.destination):
            outputs = write_derived_indexes(root, destination_id)
            for path in outputs:
                print(path)
        return 0

    if args.command == "build-notes":
        outputs = write_all_venue_notes(root)
        for path in outputs:
            print(path)
        return 0

    if args.command == "build-photo-assets":
        for destination_id in _selected_destinations(args.destination):
            if args.destination == "bali":
                manifest_path = write_photo_assets(
                    root,
                    max_images_per_photo=args.max_images_per_photo,
                )
            else:
                manifest_path = write_photo_assets(
                    root,
                    max_images_per_photo=args.max_images_per_photo,
                    destination_id=destination_id,
                )
            print(manifest_path)
        return 0

    if args.command == "build-site":
        outputs = write_static_site(root, output_dir, get_destination_config(args.destination))
        for path in outputs:
            print(path)
        return 0

    if args.command == "build-pages-site":
        outputs = write_pages_site(root)
        for path in outputs:
            print(path)
        return 0

    if args.command == "serve-site":
        serve_site(root, output_dir, host=args.host, port=args.port)
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
        merged.sort(key=lambda entry: str(entry.get("seed_id", "")))
        output_path = paths["seeds"] / "venue-seeds.json"
        write_json_file(output_path, merged)
        print(output_path)
        return 0

    parser.error("unsupported command")
    return 2
