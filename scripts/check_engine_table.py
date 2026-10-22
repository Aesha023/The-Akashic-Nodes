#!/usr/bin/env python3
"""Validation check script for BACKEND_STATUS.md engine table.

Enforces:
1. Every numeric value in the Engine Real-Run Evidence Matrix in docs/BACKEND_STATUS.md
   must appear verbatim in docs/VALIDATION.md.
2. Every line citation (VALIDATION.md §x, line n) must resolve to valid lines in
   docs/VALIDATION.md that contain the claimed numeric value(s).
Fails with exit code 1 if any check does not pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    backend_status_path = repo_root / "docs" / "BACKEND_STATUS.md"
    validation_path = repo_root / "docs" / "VALIDATION.md"

    if not backend_status_path.exists():
        print(f"Error: {backend_status_path} does not exist.")
        return 1
    if not validation_path.exists():
        print(f"Error: {validation_path} does not exist.")
        return 1

    backend_status = backend_status_path.read_text(encoding="utf-8")
    validation_content = validation_path.read_text(encoding="utf-8")
    validation_lines = validation_content.splitlines()

    # Extract engine table rows
    in_engine_table = False
    table_rows: list[str] = []
    for line in backend_status.splitlines():
        if "## 1. Engine Real-Run Evidence Matrix" in line:
            in_engine_table = True
            continue
        if in_engine_table and line.startswith("## "):
            break
        if in_engine_table and line.strip().startswith("| **"):
            table_rows.append(line)

    if not table_rows:
        print("Error: No engine table rows found in docs/BACKEND_STATUS.md.")
        return 1

    errors: list[str] = []
    print(f"Validating {len(table_rows)} engine table rows against docs/VALIDATION.md...\n")

    for idx, row in enumerate(table_rows, start=1):
        cols = [c.strip() for c in row.split("|")[1:-1]]
        if len(cols) < 4:
            continue
        engine_name = cols[0]
        evidence = cols[3]
        print(f"[{idx}] {engine_name}")

        # Remove line citation markers before extracting data numbers
        evidence_no_cit = re.sub(r"\(VALIDATION\.md[^)]*\)", "", evidence)

        # Extract numeric tokens: numbers with optional commas, decimal points, or percent signs
        raw_tokens = re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?%?\b", evidence_no_cit)
        checked_tokens = sorted(set(raw_tokens))

        for token in checked_tokens:
            if token not in validation_content:
                errors.append(
                    f"Row '{engine_name}': numeric value '{token}' NOT found in docs/VALIDATION.md"
                )
            else:
                print(f"  [OK] Number '{token}' verbatim in VALIDATION.md")

        # Parse citations of format: ... (VALIDATION.md §x, line(s) Y[-Z])
        statements = re.split(r"[;.]\s*", evidence)
        for stmt in statements:
            cit_match = re.search(
                r"\(VALIDATION\.md\s*(?:§[0-9.]+,?\s*)?lines?\s*(\d+)(?:-(\d+))?\)",
                stmt,
            )
            if not cit_match:
                continue

            start_line = int(cit_match.group(1))
            end_line = int(cit_match.group(2)) if cit_match.group(2) else start_line

            if start_line < 1 or end_line > len(validation_lines):
                errors.append(
                    f"Row '{engine_name}': Citation lines {start_line}-{end_line} "
                    f"out of range (1-{len(validation_lines)})"
                )
                continue

            target_slice = "\n".join(validation_lines[start_line - 1 : end_line])
            stmt_no_cit = stmt[: cit_match.start()]
            stmt_numbers = re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?%?\b", stmt_no_cit)

            for num in stmt_numbers:
                if num not in target_slice:
                    errors.append(
                        f"Row '{engine_name}': Number '{num}' from '{stmt_no_cit.strip()}' "
                        f"NOT found on cited lines {start_line}-{end_line} in VALIDATION.md"
                    )
                else:
                    print(
                        f"  [OK] Number '{num}' verified on cited line(s) {start_line}-{end_line}"
                    )

        print()

    # Section 11: Demo Pipeline on Tier-0 Ganga Check
    print("Validating Section 11 ('Demo pipeline on Tier-0 Ganga') in docs/VALIDATION.md...\n")
    if "## 11. Demo Pipeline on Tier-0 Ganga" not in validation_content:
        errors.append(
            "Section 11 ('Demo Pipeline on Tier-0 Ganga') missing from docs/VALIDATION.md"
        )
    else:
        sec11_text = validation_content.split("## 11. Demo Pipeline on Tier-0 Ganga")[1]
        # Mandatory banner check
        if "hypothetical scenario, tier-0 screening" not in sec11_text.lower():
            errors.append(
                "Section 11 missing mandatory label 'hypothetical scenario, Tier-0 screening'"
            )
        else:
            print(
                "  [OK] Section 11 contains mandatory "
                "'hypothetical scenario, Tier-0 screening' label"
            )

        # Verify key numbers in Section 11
        sec11_expected_numbers = [
            ("1.72", "Inundation Area (km2)"),
            ("7.73", "Max Depth (m)"),
            ("6.31", "Mean Depth (m)"),
            ("5,000.0", "Peak Flow (m3/s)"),
            ("0.035", "Manning n"),
            ("27,390.1", "Total AOI population"),
            ("2,696", "Total exposed population"),
            ("230.3", "Depth class 0.0-0.5m population"),
            ("253.3", "Depth class 0.5-1.5m population"),
            ("2,212.9", "Depth class >1.5m population"),
            ("159.54", "Total road network (km)"),
            ("5.68", "Flooded roads (km)"),
            ("93", "Total buildings in AOI"),
            ("5", "Flooded buildings"),
            ("28", "Critical facilities in AOI"),
            ("927", "Severed road edges"),
            ("108.8", "Reachable route length (m)"),
        ]
        for num, desc in sec11_expected_numbers:
            if num not in sec11_text:
                errors.append(f"Section 11: Number '{num}' ({desc}) missing from text")
            else:
                print(f"  [OK] Section 11 verified number '{num}' ({desc})")

        # Verify SHA-256 hashes
        expected_hashes = [
            (
                "d3168ae8ae742171cecd2abac607fd80d36e882e0ffb32e414f721202c900194",
                "tier0_max_depth_cog.tif",
            ),
            (
                "4fc54bcefe4e23c5f0638f775288375297091d5719d355d85f0820efe9199dbc",
                "Raw WorldPop 100m",
            ),
            (
                "5e8a8702c65299f4349e6ae738754ec8e976f0f141c21ece3dc961466f697a26",
                "worldpop_ganga_32644.tif",
            ),
            (
                "22fc11c8e56dfe9c11880e75702d48b91be5f4dbfeae712461acc66ce52976e9",
                "evacuation_routes.geojson",
            ),
            (
                "2cca3b08f6430cacd717a5dc10cee23eee06f280c3f43f0aac399df5408a3d1b",
                "tier0_envelope.geojson",
            ),
            (
                "90b890bbe659d5b1ac7dbcb9694fc57a702ed93378fa37107291aea754570b32",
                "ganga_tier0_brief.pdf",
            ),
        ]
        for h_val, h_desc in expected_hashes:
            if h_val not in sec11_text:
                errors.append(f"Section 11: Hash '{h_val}' ({h_desc}) missing from text")
            else:
                print(f"  [OK] Section 11 verified hash '{h_val[:12]}...' ({h_desc})")

    if errors:
        print(f"\nFAILED: {len(errors)} error(s) found:")
        for err in errors:
            print(f"  [FAIL] {err}")
        return 1

    print(
        "\nPASSED: All numeric values in BACKEND_STATUS.md and VALIDATION.md Section 11 "
        "are consistent and verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
