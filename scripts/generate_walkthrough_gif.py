import os

from PIL import Image

frames_dir = "artifacts/walkthrough_frames"
files = [
    "frame_01_00s_signin.png",
    "frame_02_05s_home.png",
    "frame_03_10s_results_explorer.png",
    "frame_04_15s_point_query.png",
    "frame_05_18s_settlements_drawer.png",
    "frame_06_22s_downloads_menu.png",
    "frame_07_25s_impact_analysis.png",
    "frame_08_30s_evacuation_routes.png",
]

images = []
durations = [3000, 3500, 4000, 3500, 3500, 3500, 4000, 4500]  # ms each, total ~30s

for f in files:
    p = os.path.join(frames_dir, f)
    if os.path.exists(p):
        img = Image.open(p).convert("RGB")
        # Resize slightly to keep GIF size light and fast
        img.thumbnail((1200, 750), Image.Resampling.LANCZOS)
        images.append(img)

if images:
    out_path = "artifacts/recording_walkthrough.gif"
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=durations[: len(images)],
        loop=0,
        optimize=True,
    )
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")
else:
    print("No images found.")
