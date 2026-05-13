#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Check Cobertura XML line/branch coverage for specific file suffixes."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _parse_condition_coverage(value: str) -> tuple[int, int]:
    """Parse Cobertura ``condition-coverage`` like ``50% (1/2)`` -> (covered, total)."""
    try:
        inside = value.split("(", 1)[1].split(")", 1)[0]
        covered_s, total_s = inside.split("/", 1)
        return int(covered_s), int(total_s)
    except (IndexError, ValueError):
        return 0, 0


def _print_dir(path: Path) -> None:
    try:
        if not path.exists():
            print(f"[debug] {path} (missing)")
            return
        if path.is_dir():
            entries = sorted(p.name for p in path.iterdir())
            print(f"[debug] {path} (dir) entries={entries}")
            return
        print(f"[debug] {path} (file) size={path.stat().st_size}")
    except OSError as e:
        print(f"[debug] Failed to inspect {path}: {e!r}")


def check_cobertura(
    *,
    xml_path: Path,
    filename_suffixes: list[str],
    label: str = "coverage",
    debug_dirs: bool = False,
) -> tuple[float, float, int, int, int, int, set[str]]:
    """
    Compute line and branch rates from Cobertura XML.

    for classes whose ``filename`` ends with one of ``filename_suffixes`` (after normalizing slashes).

    Returns (line_rate, branch_rate, line_covered, line_total, branch_covered, branch_total, matched_files).
    """
    if not xml_path.is_file():
        raise FileNotFoundError(f"Missing coverage XML: {xml_path.resolve()}")

    suffixes = tuple(_normalize_path(s) for s in filename_suffixes)

    def is_target(filename: str) -> bool:
        normalized = _normalize_path(filename)
        return any(normalized.endswith(s) for s in suffixes)

    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    line_total = 0
    line_covered = 0
    branch_total = 0
    branch_covered = 0
    matched_files: set[str] = set()

    for class_el in root.findall(".//class"):
        filename = class_el.attrib.get("filename")
        if not filename or not is_target(filename):
            continue
        matched_files.add(_normalize_path(filename))
        for line_el in class_el.findall(".//line"):
            line_total += 1
            hits = int(line_el.attrib.get("hits", "0") or "0")
            if hits > 0:
                line_covered += 1

            if line_el.attrib.get("branch") == "true":
                cov, tot = _parse_condition_coverage(line_el.attrib.get("condition-coverage", ""))
                branch_total += tot
                branch_covered += cov

    if not matched_files:
        raise ValueError(
            "No target files matched in Cobertura XML. "
            'Check --suffix values against <class filename="..."> in the report.'
        )

    line_rate = (line_covered / line_total) if line_total else 0.0
    branch_rate = (branch_covered / branch_total) if branch_total else 1.0

    if debug_dirs:
        cwd = Path.cwd()
        print(f"[debug] cwd={cwd}")
        _print_dir(cwd)
        _print_dir(cwd / "coverage")
        _print_dir(cwd / "files")
        _print_dir(cwd / "files" / "coverage")

    print(f"[debug] {label}: matched files:")
    for f in sorted(matched_files):
        print(f"- {f}")
    print(
        f"{label} target-only coverage: "
        f"lines={line_rate:.3%} ({line_covered}/{line_total}) "
        f"branches={branch_rate:.3%} ({branch_covered}/{branch_total})"
    )

    return line_rate, branch_rate, line_covered, line_total, branch_covered, branch_total, matched_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enforce line/branch coverage from Cobertura XML for files matching suffixes.",
    )
    parser.add_argument(
        "--xml",
        type=Path,
        required=True,
        help="Path to Cobertura XML (e.g. files/coverage/backend-anomaly-cobertura.xml).",
    )
    parser.add_argument(
        "--min-line",
        type=float,
        required=True,
        help="Minimum line coverage as a fraction in [0, 1] (e.g. 0.8 for 80%%).",
    )
    parser.add_argument(
        "--min-branch",
        type=float,
        required=True,
        help="Minimum branch coverage as a fraction in [0, 1].",
    )
    parser.add_argument(
        "--suffix",
        action="append",
        dest="suffixes",
        metavar="SUFFIX",
        required=True,
        help=(
            "Filename suffix to match (repeatable). "
            "A class is included if its filename ends with this path after normalizing slashes."
        ),
    )
    parser.add_argument(
        "--label",
        default="Target",
        help="Short label for log messages (default: %(default)s).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print cwd and common coverage directory listings before parsing.",
    )
    args = parser.parse_args(argv)

    try:
        line_rate, branch_rate, *_ = check_cobertura(
            xml_path=args.xml,
            filename_suffixes=args.suffixes,
            label=args.label,
            debug_dirs=args.debug,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    ok = True
    if line_rate < args.min_line:
        print(f"FAIL: line-rate {line_rate:.3%} < {args.min_line:.0%}")
        ok = False
    if branch_rate < args.min_branch:
        print(f"FAIL: branch-rate {branch_rate:.3%} < {args.min_branch:.0%}")
        ok = False

    if not ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
