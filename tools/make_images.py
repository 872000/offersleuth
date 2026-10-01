"""Regenerate docs/ images: hero banner, real CLI screenshot, score chart.

Run:  python3 tools/make_images.py
All images are produced programmatically with matplotlib — the screenshot
image renders the *actual* stdout of `python -m offersleuth demo`.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

matplotlib.rcParams["font.family"] = "DejaVu Sans"

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))

BG = "#0d1117"       # GitHub-dark canvas
ACCENT = "#58a6ff"   # blue
GREEN = "#3fb950"
RED = "#f85149"
AMBER = "#d29922"
FG = "#e6edf3"
MUTED = "#8b949e"


def make_hero() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    # subtle glow bars
    for i, alpha in enumerate((0.05, 0.035, 0.02)):
        ax.add_patch(Rectangle((0, 0.4 + i * 0.5), 12, 4.4 - i, color=ACCENT, alpha=alpha))

    # magnifier motif
    ax.add_patch(Circle((2.1, 2.6), 1.15, fill=False, ec=ACCENT, lw=14))
    ax.plot([2.95, 4.15], [1.85, 0.75], color=ACCENT, lw=14, solid_capstyle="round")
    ax.text(2.1, 2.55, "?", fontsize=64, weight="bold", color=ACCENT,
            ha="center", va="center", alpha=0.9)

    ax.text(4.9, 3.55, "OfferSleuth", fontsize=56, weight="bold", color=FG, va="center")
    ax.text(4.9, 2.75, "Read every job posting like a detective.", fontsize=19,
            color=MUTED, va="center")
    chips = [("Red-flag detector", RED), ("Salary sanity-check", GREEN), ("Resume tailoring", AMBER)]
    x = 4.9
    for label, color in chips:
        ax.text(x, 1.85, f"  {label}  ", fontsize=13, color=BG, va="center",
                bbox=dict(boxstyle="round,pad=0.35", fc=color, ec="none"))
        x += len(label) * 0.115 + 0.75

    fig.tight_layout(pad=0.4)
    fig.savefig(DOCS / "hero.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print("wrote docs/hero.png")


def _real_cli_output() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "offersleuth", "demo", "scammy"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def make_screenshot() -> None:
    raw = _real_cli_output()
    # wrap long lines for the fixed-width render
    lines: list[str] = []
    for line in raw.splitlines():
        lines.extend(textwrap.wrap(line, width=78) or [""])
    lines = lines[:52]

    n = len(lines)
    fig, ax = plt.subplots(figsize=(10.5, 0.42 * n + 1.0), dpi=130)
    fig.patch.set_facecolor("#010409")
    ax.set_facecolor("#0d1117")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, n + 2)
    ax.axis("off")

    # terminal chrome
    ax.text(0.02, n + 1.35, "\u25cf \u25cf \u25cf", fontsize=13, color=MUTED, va="center")
    ax.text(0.5, n + 1.35, "parth@dev: ~/offersleuth  —  python -m offersleuth demo scammy",
            fontsize=10, color=MUTED, ha="center", va="center", family="monospace")

    for i, line in enumerate(lines):
        y = n - i
        color = FG
        if "[CRITICAL]" in line:
            color = RED
        elif "[HIGH]" in line:
            color = "#ff9e64"
        elif "[MEDIUM]" in line:
            color = AMBER
        elif line.startswith("  Score:"):
            color = ACCENT
        ax.text(0.02, y, line, fontsize=9.2, color=color, va="top", family="monospace")

    ax.text(0.02, 0.55, "docs/screenshot.png — rendered from real `offersleuth demo` stdout",
            fontsize=8, color=MUTED, family="monospace")
    fig.savefig(DOCS / "screenshot.png", facecolor="#010409", bbox_inches="tight")
    plt.close(fig)
    print("wrote docs/screenshot.png")


def make_scores() -> None:
    from offersleuth import analyze

    samples = ["good", "mediocre", "scammy"]
    scores, grades = [], []
    for name in samples:
        report = analyze((ROOT / "demo_data" / "sample_jds" / f"{name}.md").read_text())
        scores.append(report.score)
        grades.append(report.grade)
    colors = [GREEN if s >= 75 else AMBER if s >= 40 else RED for s in scores]

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=130)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    bars = ax.bar(samples, scores, color=colors, width=0.55, edgecolor=FG, linewidth=0.8)
    ax.set_ylim(0, 110)
    ax.set_ylabel("OfferSleuth score", color=MUTED)
    ax.set_title("How the bundled sample postings score", color=FG, fontsize=13, pad=12)
    ax.tick_params(colors=MUTED)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.yaxis.grid(True, color="#21262d", linewidth=0.6)
    ax.set_axisbelow(True)
    for bar, score, grade in zip(bars, scores, grades):
        ax.text(bar.get_x() + bar.get_width() / 2, score + 2, f"{score}  ({grade})",
                ha="center", color=FG, fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(DOCS / "scores.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print("wrote docs/scores.png")


if __name__ == "__main__":
    make_hero()
    make_screenshot()
    make_scores()
