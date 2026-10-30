"""PravahX Remote Compute Worker Adapter (Google Colab / GPU VM).

Usage:
    python scripts/remote_worker.py --api-url http://localhost:8000/api/v1 --engine delft3d
    python scripts/remote_worker.py --api-url http://localhost:8000/api/v1 --engine dualsphysics
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def post_json(url: str, data: dict, api_key: str | None = None) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key or "",
            "User-Agent": "PravahX-Worker/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str, api_key: str | None = None) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "X-API-Key": api_key or "",
            "User-Agent": "PravahX-Worker/1.0",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="PravahX Remote Compute Worker")
    parser.add_argument(
        "--api-url", default="http://127.0.0.1:8000/api/v1", help="Base URL of PravahX API"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("PRAVAHX_API_KEY", "dev_worker_key"),
        help="API authentication key",
    )
    parser.add_argument(
        "--engine",
        choices=["delft3d", "dualsphysics"],
        required=True,
        help="Engine type to serve",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run one poll loop and exit (for testing)"
    )

    args = parser.parse_args()

    worker_id = f"worker_{args.engine}_{socket.gethostname()}_{os.getpid()}"
    print(f"[*] Starting PravahX Worker: {worker_id}")
    print(f"[*] Engine: {args.engine} | System: {platform.system()} {platform.machine()}")

    # 1. Register with coordinator
    reg_url = f"{args.api_url}/workers/register"
    try:
        reg_resp = post_json(
            reg_url,
            {
                "worker_id": worker_id,
                "engine": args.engine,
                "hostname": socket.gethostname(),
                "capabilities": {
                    "os": platform.system(),
                    "cpu_count": os.cpu_count(),
                    "python": sys.version.split()[0],
                },
            },
            args.api_key,
        )
        print(f"[+] Successfully registered with coordinator: {reg_resp}")
    except Exception as exc:
        print(f"[-] Registration failed: {exc}", file=sys.stderr)
        if args.once:
            sys.exit(1)

    # 2. Polling loop
    poll_count = 0
    while True:
        poll_count += 1
        try:
            pull_url = f"{args.api_url}/workers/jobs/pull?engine={args.engine}"
            pull_resp = get_json(pull_url, args.api_key)
            job = pull_resp.get("job")

            if job:
                print(f"[!] Claimed job: {job.get('id')} ({job.get('scenario_id')})")
                prog_url = f"{args.api_url}/workers/jobs/{job.get('id')}/progress"
                post_json(
                    prog_url,
                    {
                        "progress_percent": 25.0,
                        "stage": "executing_hydrodynamics",
                        "log_line": f"Worker {worker_id} computing timesteps...",
                    },
                    args.api_key,
                )
                time.sleep(1)
            else:
                if poll_count % 5 == 1:
                    print(f"[*] Worker idle. Waiting for {args.engine} jobs on queue...")

        except Exception as exc:
            print(f"[!] Polling warning: {exc}")

        if args.once:
            print("[*] Worker exit (--once flag).")
            break

        time.sleep(5)


if __name__ == "__main__":
    main()
