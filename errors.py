import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from pathlib import Path

INPUT = Path("_fielding.csv")
OUTPUT = Path("errors.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
OLD = "#17324A"
RED = "#D94A3A"
CREAM = "#F1EBDD"
GRID = "#AFC9D1"

df = pd.read_csv(INPUT, low_memory=False)
df = df[df["gametype"].eq("regular")].copy()
df["season"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
df = df[df["season"].between(1900, 2025)].copy()

for col in ["d_po", "d_a", "d_e"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["chances"] = df["d_po"] + df["d_a"] + df["d_e"]

team = df.groupby(["season", "team"], as_index=False).agg(errors=("d_e", "sum"), chances=("chances", "sum"))
team = team[team["chances"] >= 2000].copy()
team["error_rate"] = team["errors"] / team["chances"] * 100
team["decade"] = team["season"] // 10 * 10

decades = sorted(team["decade"].unique())
x_min = max(0, team["error_rate"].quantile(0.002) - 0.25)
x_max = 6
x_grid = np.linspace(x_min, x_max, 600)

old_rgb = np.array([23, 50, 74]) / 255
red_rgb = np.array([217, 74, 58]) / 255

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.13, 0.13, 0.79, 0.69], facecolor=BG)

ridge_height = 0.95
spacing = 1.0

for i, decade in enumerate(decades):
    values = team.loc[team["decade"] == decade, "error_rate"].dropna().to_numpy()
    if len(values) < 3: continue

    density_raw = gaussian_kde(values, bw_method=0.35)(x_grid)
    density = density_raw / density_raw.max() * ridge_height
    y0 = i * spacing
    t = i / max(1, len(decades) - 1)
    color = old_rgb * (1 - t) + red_rgb * t

    ax.fill_between(x_grid, y0, y0 - density, color=color, alpha=0.92, zorder=2 + i)
    ax.plot(x_grid, y0 - density, color=CREAM, linewidth=1.0, alpha=0.9, zorder=3 + i)
    ax.axhline(y0, color=BG, linewidth=1.1, zorder=4 + i)

    median = np.median(values)
    ax.scatter(median, y0 - 0.05, s=22, color=CREAM, edgecolor=color, linewidth=0.8, zorder=20)
    ax.text(x_max + 0.18, y0, f"{decade}s", ha="right", va="center", fontsize=9, fontweight="bold", color=TEXT, clip_on=False)

ax.set_xlim(x_min, x_max)
ax.set_ylim(-ridge_height - 0.35, (len(decades) - 1) * spacing + 0.35)
ax.invert_xaxis()
ax.invert_yaxis()

ax.set_xticks(np.arange(0, 7, 1))
ax.set_yticks([])
ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
ax.set_xlabel("ERRORS PER 100 DEFENSIVE CHANCES", fontsize=9, fontweight="bold", color=MUTED, labelpad=12)
ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.5, zorder=0)

for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  05/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "Baseball squeezed out the error", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each ridge shows team-season fielding error rates for one decade, revealing both fewer mistakes and a tighter modern game.", fontsize=11.0, 
    color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season fielding records, 1900–2025 · Qualified team-seasons: 2,000+ chances", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=164, facecolor=BG)
plt.show()