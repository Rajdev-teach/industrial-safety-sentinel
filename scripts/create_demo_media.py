from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_sentinel.config import DB_PATH  # noqa: E402
from safety_sentinel.database import SafetyDatabase  # noqa: E402

BG, PANEL, GRID = "#07111d", "#0d1b2a", "#1f3549"
TEXT, MUTED, CYAN, GREEN, RED, AMBER = "#e8f1f7", "#8ca4b7", "#22d3ee", "#34d399", "#fb7185", "#fbbf24"


def draw_frame(readings: list[dict], alerts: list[dict], metrics: dict, path: Path, frame: int = 0) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    grid = fig.add_gridspec(12, 12, left=.04, right=.96, top=.92, bottom=.06, hspace=.65, wspace=.45)
    fig.text(.04, .955, "REAL-TIME INDUSTRIAL INTELLIGENCE", color=CYAN, fontsize=8, weight="bold")
    fig.text(.04, .92, "Industrial Safety Sentinel", color=TEXT, fontsize=23, weight="bold")
    fig.text(.825, .935, "●  LIVE MONITORING", color=GREEN, fontsize=10, weight="bold")

    values = [("TOTAL READINGS", metrics["readings"] + frame), ("ACTIVE ALERTS", metrics["open"]),
              ("CRITICAL EVENTS", metrics["critical"]), ("SYSTEM STATUS", "ONLINE")]
    for idx, (label, value) in enumerate(values):
        ax = fig.add_subplot(grid[0:2, idx*3:(idx+1)*3]); style(ax)
        ax.text(.06, .72, label, color=MUTED, fontsize=8, transform=ax.transAxes)
        ax.text(.06, .23, str(value), color=GREEN if idx == 3 else TEXT, fontsize=22 if idx < 3 else 16, weight="bold", transform=ax.transAxes)

    ax = fig.add_subplot(grid[2:7, 0:8]); style(ax); ax.set_title("Live Sensor Telemetry", loc="left", color=TEXT, fontsize=11, weight="bold", pad=12)
    x = np.arange(len(readings)); ax.plot(x, [r["temperature_c"] for r in readings], color=CYAN, lw=2, label="Temperature")
    ax.plot(x, [r["noise_db"] for r in readings], color="#a78bfa", lw=2, label="Noise")
    ax.plot(x, [r["vibration_mm_s"]*5 for r in readings], color=RED, lw=2, label="Vibration ×5")
    ax.grid(color=GRID, alpha=.7); ax.tick_params(colors=MUTED, labelsize=7); ax.legend(frameon=False, labelcolor=MUTED, fontsize=7, loc="upper left", ncol=3)

    latest = readings[-1]
    ax = fig.add_subplot(grid[2:7, 8:12]); style(ax); ax.set_title("Current Conditions", loc="left", color=TEXT, fontsize=11, weight="bold", pad=12)
    conditions = [("TEMPERATURE", f'{latest["temperature_c"]:.1f} °C'), ("VIBRATION", f'{latest["vibration_mm_s"]:.1f} mm/s'),
                  ("FORKLIFT SPEED", f'{latest["forklift_speed_mph"]:.1f} mph'), ("NOISE", f'{latest["noise_db"]:.1f} dB')]
    for i, (label, value) in enumerate(conditions):
        x0=.05+(i%2)*.49; y0=.66-(i//2)*.43
        ax.add_patch(plt.Rectangle((x0,y0),.44,.3,facecolor="#091521",edgecolor=GRID,transform=ax.transAxes))
        ax.text(x0+.04,y0+.2,label,color=MUTED,fontsize=7,transform=ax.transAxes); ax.text(x0+.04,y0+.07,value,color=TEXT,fontsize=13,weight="bold",transform=ax.transAxes)

    ax = fig.add_subplot(grid[7:12, 0:8]); style(ax); ax.set_title("Safety Alerts", loc="left", color=TEXT, fontsize=11, weight="bold", pad=12)
    for i, alert in enumerate(alerts[:5]):
        y=.86-i*.18; color=RED if alert["severity"]=="CRITICAL" else AMBER
        ax.text(.03,y,alert["severity"],color=color,fontsize=7,weight="bold",transform=ax.transAxes)
        ax.text(.18,y,alert["message"][:68],color=TEXT,fontsize=8,transform=ax.transAxes)
        ax.text(.88,y,alert["zone"],color=MUTED,fontsize=7,ha="right",transform=ax.transAxes)
        ax.plot([.03,.97],[y-.08,y-.08],color=GRID,lw=.7,transform=ax.transAxes)

    ax = fig.add_subplot(grid[7:12, 8:12]); style(ax); ax.set_title("Computer Vision Status", loc="left", color=TEXT, fontsize=11, weight="bold", pad=12)
    for z in np.linspace(.08,.92,7): ax.plot([z,z],[.08,.9],color=GRID,lw=.5,transform=ax.transAxes); ax.plot([.06,.94],[z,z],color=GRID,lw=.5,transform=ax.transAxes)
    ax.add_patch(plt.Rectangle((.39,.28),.23,.48,fill=False,edgecolor=GREEN,lw=2,transform=ax.transAxes)); ax.text(.405,.7,"WORKER-ANON",color=GREEN,fontsize=6,transform=ax.transAxes)
    ax.plot([.08,.92],[.2,.2],color=RED,lw=1.5,ls="--",transform=ax.transAxes); ax.text(.5,.13,"RESTRICTED ZONE",color=RED,fontsize=7,ha="center",transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    path.parent.mkdir(parents=True, exist_ok=True); fig.savefig(path, dpi=120, facecolor=BG); plt.close(fig)


def style(ax):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values(): spine.set_color(GRID)
    ax.set_xticks([]); ax.set_yticks([])


def main() -> None:
    db = SafetyDatabase(DB_PATH); readings = db.latest_readings(40); alerts = db.latest_alerts(10); metrics = db.metrics()
    docs, frames = ROOT / "docs", ROOT / "docs" / "frames"; docs.mkdir(exist_ok=True); frames.mkdir(exist_ok=True)
    draw_frame(readings, alerts, metrics, docs / "dashboard-overview.png")
    for i in range(36): draw_frame(readings, alerts[i % max(len(alerts), 1):] + alerts[:i % max(len(alerts), 1)], metrics, frames / f"frame-{i:03d}.png", i)
    subprocess.run(["ffmpeg", "-y", "-framerate", "6", "-i", str(frames / "frame-%03d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(docs / "industrial-safety-demo.mp4")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for frame in frames.glob("*.png"): frame.unlink()
    frames.rmdir()
    print(f"Created {docs / 'dashboard-overview.png'} and demo video")


if __name__ == "__main__": main()
