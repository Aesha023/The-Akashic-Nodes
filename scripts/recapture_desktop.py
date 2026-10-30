import asyncio
import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARTIFACTS_DIR = Path(
    r"C:\Users\Krishna\.gemini\antigravity-ide\brain\6b2e8c01-33c5-4da5-99e7-4fc87ac35236"
)


async def send_cdp(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 1000000
    msg = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})


async def capture_page(ws, url, out_path, wait_sec=3.0):
    await send_cdp(ws, "Runtime.evaluate", {"expression": f"window.location.href = '{url}';"})
    await asyncio.sleep(wait_sec)
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = res.get("data")
    if data:
        img_bytes = base64.b64decode(data)
        out_path.write_bytes(img_bytes)
        print(f"[OK] Saved {out_path.name} ({len(img_bytes)} bytes)", flush=True)


async def main():
    temp_dir = tempfile.mkdtemp()
    port = 9555
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--disable-gpu",
        "--no-first-run",
        "--hide-scrollbars",
        f"--user-data-dir={temp_dir}",
        "http://127.0.0.1:3000/",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as r:
                    tabs = json.loads(r.read().decode())
                    for tab in tabs:
                        if tab.get("type") == "page" and tab.get("webSocketDebuggerUrl"):
                            ws_url = tab["webSocketDebuggerUrl"]
                            break
                    if ws_url:
                        break
            except Exception:
                await asyncio.sleep(0.3)

        if not ws_url:
            raise RuntimeError("Could not find page target")

        async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")
            await send_cdp(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 1440,
                    "height": 900,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                },
            )
            # Initial wait for bundle load
            await asyncio.sleep(3.0)

            # 1. Landing Desktop
            await capture_page(
                ws,
                "http://127.0.0.1:3000/#landing",
                ARTIFACTS_DIR / "c1_landing_desktop.png",
                wait_sec=3.5,
            )

            # 2. SignIn Desktop
            await capture_page(
                ws,
                "http://127.0.0.1:3000/#signin",
                ARTIFACTS_DIR / "c1_signin_desktop.png",
                wait_sec=2.0,
            )

            # 3. Home Desktop
            await capture_page(
                ws,
                "http://127.0.0.1:3000/#home",
                ARTIFACTS_DIR / "c1_home_desktop.png",
                wait_sec=2.0,
            )

            # 4. Results Explorer Desktop
            await capture_page(
                ws,
                "http://127.0.0.1:3000/#f05_results_explorer",
                ARTIFACTS_DIR / "c1_results_floodmap_desktop.png",
                wait_sec=3.5,
            )

            # 5. App Shell Presentation Mode Desktop
            await capture_page(
                ws,
                "http://127.0.0.1:3000/#f01_mission_control",
                ARTIFACTS_DIR / "c1_appshell_presentation_desktop.png",
                wait_sec=2.0,
            )

            # 6. App Shell Operational Mode Desktop
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": "localStorage.setItem('pravahx_presentation_mode', 'false'); window.location.reload();"
                },
            )
            await asyncio.sleep(2.5)
            await capture_page(
                ws,
                "http://127.0.0.1:3000/#f01_mission_control",
                ARTIFACTS_DIR / "c1_appshell_operational_desktop.png",
                wait_sec=2.0,
            )

            # Restore localStorage
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "localStorage.setItem('pravahx_presentation_mode', 'true');"},
            )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
