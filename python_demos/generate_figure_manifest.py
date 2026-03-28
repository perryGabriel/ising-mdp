#!/usr/bin/env python3
"""Generate a lightweight manifest of report artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List

TRACKED_SUFFIXES = {".png", ".gif", ".csv", ".json"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate artifact manifest JSON for report reproducibility.")
    parser.add_argument("--artifact-prefix", default="artifacts")
    parser.add_argument("--output", default="reports/figure_manifest.json")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(artifact_prefix: Path) -> Dict[str, List[Dict[str, str]]]:
    entries: List[Dict[str, str]] = []
    for path in sorted(artifact_prefix.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TRACKED_SUFFIXES:
            continue
        rel = path.relative_to(artifact_prefix.parent)
        entries.append(
            {
                "path": str(rel),
                "bytes": str(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    return {"artifacts": entries}


def main() -> None:
    args = parse_args()
    artifact_prefix = Path(args.artifact_prefix)
    manifest = build_manifest(artifact_prefix)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest to {out} with {len(manifest['artifacts'])} entries")


if __name__ == "__main__":
    main()
