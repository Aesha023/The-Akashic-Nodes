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

    if errors:
        print(f"FAILED: {len(errors)} error(s) found:")
        for err in errors:
            print(f"  [FAIL] {err}")
        return 1

    print(
        "PASSED: All numeric values in BACKEND_STATUS.md engine table appear verbatim "
        "in VALIDATION.md."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
