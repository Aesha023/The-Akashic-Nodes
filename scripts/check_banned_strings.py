"""
CI Check: Scan built frontend assets and source files for banned strings.
Banned terms:
- HEC-RAS
- H100
- TFLOPS
- ISO-14065
- NIDM
- FIPS
- NTRO
- National Technical Intelligence
- Sovereign Defense
- Sentinel-1B
- ₹
- Mullaperiyar
- Tehri
- Sardar Sarovar
- Hirakud
- Teesta-III
- South Lhonak
"""

import os
import sys
from pathlib import Path

BANNED_STRINGS = [
    "HEC-RAS",
    "H100",
    "TFLOPS",
    "ISO-14065",
    "NIDM",
    "FIPS",
    "NTRO",
    "National Technical Intelligence",
    "Sovereign Defense",
    "Sentinel-1B",
    "₹",
    "Mullaperiyar",
    "Tehri",
    "Sardar Sarovar",
    "Hirakud",
    "Teesta-III",
    "South Lhonak",
]


def check_file(file_path: Path):
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations

    for banned in BANNED_STRINGS:
        if banned in content:
            violations.append((banned, file_path))
    return violations


def main():
    repo_root = Path(__file__).resolve().parent.parent
    frontend_dir = repo_root / "frontend"
    dist_dir = frontend_dir / "dist"
    src_dir = frontend_dir / "src"

    all_violations = []

    # Check dist
    if dist_dir.exists():
        for root, _, files in os.walk(dist_dir):
            for file in files:
                p = Path(root) / file
                if p.suffix in [".js", ".html", ".css", ".json"]:
                    all_violations.extend(check_file(p))

    # Check src
    if src_dir.exists():
        for root, _, files in os.walk(src_dir):
            for file in files:
                p = Path(root) / file
                if p.suffix in [".ts", ".tsx", ".js", ".jsx", ".html", ".css"]:
                    # Skip openapi.json if it contains generated types from other schemas unless violates
                    if file in ["openapi.json", "generated.ts"]:
                        continue
                    all_violations.extend(check_file(p))

    if all_violations:
        print(f"[FAIL] Found {len(all_violations)} banned string violations:")
        for banned, path in all_violations:
            print(f"  - '{banned}' in {path.relative_to(repo_root)}")
        sys.exit(1)
    else:
        print("[PASS] Zero banned strings found across frontend bundle and source code.")
        sys.exit(0)


if __name__ == "__main__":
    main()
