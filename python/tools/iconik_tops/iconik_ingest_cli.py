#!/usr/bin/env python3
"""CLI for recursive USD discovery and Iconik ingest (validate before TOPs)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import List

# Allow running as script from repo root on PYTHONPATH
_SCRIPT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, _SCRIPT_ROOT)

from integrations.usd_discovery import UsdDiscoveryConfig, discover_usd_files
from integrations.workflows.ingest_usd_to_iconik import IngestRequest, ingest_usd_to_iconik


def _parse_globs(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace(",", ";").split(";") if part.strip()]


def _discover(args) -> list:
    cfg = UsdDiscoveryConfig(
        mode=args.mode,
        recursive=bool(args.recursive),
        include_globs=_parse_globs(args.include_globs),
        exclude_globs=_parse_globs(args.exclude_globs),
        max_items=int(args.max_items or 0),
    )
    return discover_usd_files(args.root, cfg)


def cmd_scan(args) -> int:
    hits = _discover(args)
    if args.json:
        payload = [
            {
                "usd_path": h.usd_path,
                "asset_name": h.asset_name,
                "folder_path": h.folder_path,
                "selection_reason": h.selection_reason,
                "file_size": h.file_size,
                "kb3d_asset_code": h.kb3d_asset_code,
            }
            for h in hits
        ]
        print(json.dumps(payload, indent=2))
    else:
        print(f"Found {len(hits)} USD file(s) under {args.root}")
        for h in hits:
            print(f"  [{h.selection_reason}] {h.usd_path}")
    return 0


def cmd_ingest(args) -> int:
    hits = _discover(args)
    if not hits:
        print(f"No USD files found under {args.root}", file=sys.stderr)
        return 1

    if args.limit and args.limit > 0:
        hits = hits[: args.limit]

    results = []
    ok = 0
    failed = 0
    skipped = 0

    for index, hit in enumerate(hits, start=1):
        print(f"[{index}/{len(hits)}] {hit.usd_path}")
        result = ingest_usd_to_iconik(
            IngestRequest(
                usd_path=hit.usd_path,
                asset_name=hit.asset_name,
                discovery_mode=args.mode,
                dry_run=bool(args.dry_run),
                on_exists=args.on_exists,
                ftrack_task_id=args.ftrack_task_id or None,
                extra_metadata={
                    "selection_reason": hit.selection_reason,
                    **({"kb3d_asset_code": hit.kb3d_asset_code} if hit.kb3d_asset_code else {}),
                },
            )
        )
        row = {
            "usd_path": hit.usd_path,
            "asset_name": hit.asset_name,
            "success": result.success,
            "skipped": result.skipped,
            "iconik_asset_id": result.iconik_asset_id or "",
            "message": result.message,
        }
        results.append(row)
        if result.skipped:
            skipped += 1
            print(f"  SKIP — {result.message}")
        elif result.success:
            ok += 1
            print(f"  OK — {result.message}")
        else:
            failed += 1
            print(f"  FAIL — {result.message}", file=sys.stderr)

    if args.manifest:
        manifest_path = os.path.abspath(args.manifest)
        os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["usd_path", "asset_name", "success", "skipped", "iconik_asset_id", "message"],
            )
            writer.writeheader()
            writer.writerows(results)
        print(f"Manifest written: {manifest_path}")

    print(f"Done — ok={ok} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--root", required=True, help="Library root folder to scan")
    shared.add_argument(
        "--mode",
        choices=["primary", "all", "glob"],
        default="primary",
        help="USD selection mode (default: primary KB3D deliverable)",
    )
    shared.add_argument("--recursive", action="store_true", default=True)
    shared.add_argument("--no-recursive", dest="recursive", action="store_false")
    shared.add_argument("--include-globs", default="", help="Semicolon-separated include globs (glob mode)")
    shared.add_argument("--exclude-globs", default="", help="Semicolon-separated exclude globs")
    shared.add_argument("--max-items", type=int, default=0, help="Cap discovery count (0 = unlimited)")
    shared.add_argument(
        "--on-exists",
        choices=["skip", "update", "new_version"],
        default="update",
        help="Behavior when asset already exists in Iconik",
    )
    shared.add_argument("--ftrack-task-id", default="", help="Optional ftrack task UUID for metadata")
    shared.add_argument("--dry-run", action="store_true", help="Discover/log only; no Iconik writes")

    parser = argparse.ArgumentParser(description="Discover USD files and ingest to Iconik")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", parents=[shared], help="List USD files that would be ingested")
    scan_p.add_argument("--json", action="store_true", help="JSON output")

    ingest_p = sub.add_parser("ingest", parents=[shared], help="Upload discovered USD files to Iconik")
    ingest_p.add_argument("--manifest", default="", help="CSV manifest output path")
    ingest_p.add_argument("--limit", type=int, default=0, help="Max files to ingest (0 = all discovered)")

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        return cmd_scan(args)
    if args.command == "ingest":
        return cmd_ingest(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
