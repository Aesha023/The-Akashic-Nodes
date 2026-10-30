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
ARTIFACTS_DIR = Path(r"C:\Users\Krishna\.gemini\antigravity-ide\brain\6b2e8c01-33c5-4da5-99e7-4fc87ac35236")

async def send_cdp(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 1000000
    msg = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})

async def capture_target(url, output_path, width=1440, height=900, is_mobile=False, setup_js=None):
    temp_dir = tempfile.mkdtemp()
    port = 9444
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--disable-gpu",
        "--no-first-run",
        "--hide-scrollbars",
        f"--user-data-dir={temp_dir}",
        "about:blank",
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
            raise RuntimeError("Could not find page target on Chrome debugging port")

        async with websockets.connect(ws_url, max_size=25 * 1024 * 1024) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": is_mobile,
            })
            await send_cdp(ws, "Page.navigate", {"url": url})
            await asyncio.sleep(2.5)

            if setup_js:
                await send_cdp(ws, "Runtime.evaluate", {"expression": setup_js})
                await asyncio.sleep(1.0)

            res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            if data:
                img_bytes = base64.b64decode(data)
                output_path.write_bytes(img_bytes)
                print(f"[OK] Saved {output_path.name} ({len(img_bytes)} bytes)", flush=True)
            else:
                print(f"[ERROR] Failed capturing screenshot for {url}", flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

async def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    print("Capturing shell screenshots in Presentation and Operational modes...", flush=True)

    # 5. Mission Control Shell Presentation Mode (Demo Content ON)
    await capture_target(
        "http://127.0.0.1:3000/#f01_mission_control",
        ARTIFACTS_DIR / "c1_appshell_presentation.png",
        width=1440,
        height=900,
        setup_js="localStorage.setItem('pravahx_presentation_mode', 'true');",
    )

    # 6. Mission Control Shell Operational Mode (Demo Content OFF)
    await capture_target(
        "http://127.0.0.1:3000/#f01_mission_control",
        ARTIFACTS_DIR / "c1_appshell_operational.png",
        width=1440,
        height=900,
        setup_js="localStorage.setItem('pravahx_presentation_mode', 'false'); window.location.reload();",
    )

    print("Shell screenshots saved!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
