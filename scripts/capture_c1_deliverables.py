import asyncio
import base64
import io
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets
from PIL import Image

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


async def capture_screenshot(ws, output_path):
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = res.get("data")
    if data:
        img_bytes = base64.b64decode(data)
        output_path.write_bytes(img_bytes)
        print(f"[OK] Saved {output_path.name} ({len(img_bytes)} bytes)", flush=True)
        return Image.open(io.BytesIO(img_bytes))
    return None


async def capture_all_screenshots():
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
        # Wait for Chrome CDP port
        ws_url = None
        for _ in range(40):
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
                await asyncio.sleep(0.25)

        if not ws_url:
            raise RuntimeError("Could not find page target on Chrome debugging port")

        async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
            await send_cdp(ws, "Page.enable")
            await send_cdp(ws, "Runtime.enable")

            # -------------------------------------------------------------
            # 1. Desktop Screenshots (1440x900)
            # -------------------------------------------------------------
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

            # Landing Desktop
            print("Capturing Landing Desktop...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#landing"})
            await asyncio.sleep(3.5)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_landing_desktop.png")

            # SignIn Desktop
            print("Capturing SignIn Desktop...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#signin"})
            await asyncio.sleep(2.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_signin_desktop.png")

            # Home Desktop
            print("Capturing Home Desktop...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#home"})
            await asyncio.sleep(2.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_home_desktop.png")

            # Results Explorer (Flood Map) Desktop
            print("Capturing Results Explorer Desktop...", flush=True)
            await send_cdp(
                ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#f05_results_explorer"}
            )
            await asyncio.sleep(3.5)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_results_floodmap_desktop.png")

            # App Shell Presentation Mode
            print("Capturing App Shell Presentation Mode...", flush=True)
            await send_cdp(
                ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#f01_mission_control"}
            )
            await asyncio.sleep(2.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_appshell_presentation_desktop.png")

            # App Shell Operational Mode (toggle presentation off in localStorage)
            print("Capturing App Shell Operational Mode...", flush=True)
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": "localStorage.setItem('pravahx_presentation_mode', 'false'); window.location.reload();"
                },
            )
            await asyncio.sleep(2.5)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_appshell_operational_desktop.png")

            # Restore presentation mode
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "localStorage.setItem('pravahx_presentation_mode', 'true');"},
            )

            # -------------------------------------------------------------
            # 2. Mobile Screenshots (360x780)
            # -------------------------------------------------------------
            print("Configuring mobile viewport 360x780...", flush=True)
            await send_cdp(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 360,
                    "height": 780,
                    "deviceScaleFactor": 2,
                    "mobile": True,
                },
            )

            # Landing Mobile
            print("Capturing Landing Mobile...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#landing"})
            await asyncio.sleep(3.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_landing_mobile.png")

            # SignIn Mobile
            print("Capturing SignIn Mobile...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#signin"})
            await asyncio.sleep(2.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_signin_mobile.png")

            # Home Mobile
            print("Capturing Home Mobile...", flush=True)
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#home"})
            await asyncio.sleep(2.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_home_mobile.png")

            # Results Explorer Mobile
            print("Capturing Results Explorer Mobile...", flush=True)
            await send_cdp(
                ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#f05_results_explorer"}
            )
            await asyncio.sleep(3.0)
            await capture_screenshot(ws, ARTIFACTS_DIR / "c1_results_floodmap_mobile.png")

            # -------------------------------------------------------------
            # 3. Screen Recording 1: Landing Scroll Story (GIF)
            # -------------------------------------------------------------
            print("Recording Landing Scroll Story GIF...", flush=True)
            await send_cdp(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 1280,
                    "height": 720,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                },
            )
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#landing"})
            await asyncio.sleep(2.5)

            frames = []
            # Frame 1: Hero
            img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
            if img:
                frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            # Scroll through each section slowly
            scroll_positions = [300, 600, 950, 1300, 1700, 2100, 2600, 3100, 3600, 4100, 4600, 5100]
            for pos in scroll_positions:
                await send_cdp(
                    ws,
                    "Runtime.evaluate",
                    {"expression": f"window.scrollTo({{ top: {pos}, behavior: 'smooth' }});"},
                )
                await asyncio.sleep(0.7)
                img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
                if img:
                    frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            if frames:
                gif_path = ARTIFACTS_DIR / "c1_landing_scroll_story.gif"
                frames[0].save(
                    str(gif_path),
                    save_all=True,
                    append_images=frames[1:],
                    duration=650,  # ~650ms per frame
                    loop=0,
                    optimize=True,
                )
                print(
                    f"[OK] Generated {gif_path.name} with {len(frames)} frames ({gif_path.stat().st_size} bytes)",
                    flush=True,
                )

            # -------------------------------------------------------------
            # 4. Screen Recording 2: Sign-In -> Home -> Flood Map Flow (GIF)
            # -------------------------------------------------------------
            print("Recording Sign-in -> Home -> Flood Map Flow GIF...", flush=True)
            flow_frames = []

            # Step 1: Sign in page
            await send_cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:3000/#signin"})
            await asyncio.sleep(1.5)
            img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            # Step 2: Click Sign In Button
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "document.getElementById('signin-submit-btn')?.click();"},
            )
            await asyncio.sleep(1.8)
            img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            # Step 3: On Home screen, hover over Card 2
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "document.getElementById('open-flood-map-btn')?.focus();"},
            )
            await asyncio.sleep(1.2)
            img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            # Step 4: Click Open Flood Map
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "document.getElementById('open-flood-map-btn')?.click();"},
            )
            await asyncio.sleep(3.0)
            img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            # Step 5: Scroll down results page to show exposed villages table
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "window.scrollTo({ top: 400, behavior: 'smooth' });"},
            )
            await asyncio.sleep(1.5)
            img = await capture_screenshot(ws, ARTIFACTS_DIR / "temp_frame.png")
            if img:
                flow_frames.append(img.resize((854, 480), Image.Resampling.LANCZOS))

            if flow_frames:
                flow_gif_path = ARTIFACTS_DIR / "c1_signin_home_map_flow.gif"
                flow_frames[0].save(
                    str(flow_gif_path),
                    save_all=True,
                    append_images=flow_frames[1:],
                    duration=900,
                    loop=0,
                    optimize=True,
                )
                print(
                    f"[OK] Generated {flow_gif_path.name} with {len(flow_frames)} frames ({flow_gif_path.stat().st_size} bytes)",
                    flush=True,
                )

            # Cleanup temp file
            temp_frame = ARTIFACTS_DIR / "temp_frame.png"
            if temp_frame.exists():
                temp_frame.unlink()

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(capture_all_screenshots())
