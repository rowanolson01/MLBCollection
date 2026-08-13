import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from pathlib import Path

INPUT = Path("_pitching.csv")
OUTPUT = Path("offense.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
RED = "#D94A3A"
GRID = "#AFC9D1"
POINT = "#F1EBDD"

df = pd.read_csv(INPUT, low_memory=False)
df["season"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
df = df[df["season"].between(1900, 2025)].copy()
if "gametype" in df.columns: df = df[df["gametype"].eq("regular")].copy()
for col in ["p_k", "p_hr", "p_r"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

season = df.groupby("season", as_index=False).agg(games=("gid", "nunique"), strikeouts=("p_k", "sum"), home_runs=("p_hr", "sum"), runs=("p_r", "sum"))
season["so_per_game"] = season["strikeouts"] / season["games"]
season["hr_per_game"] = season["home_runs"] / season["games"]
season["runs_per_game"] = season["runs"] / season["games"]
season["period_start"] = ((season["season"] - 1900) // 5) * 5 + 1900
season["period_end"] = np.minimum(season["period_start"] + 4, 2025)

agg = season.groupby(["period_start", "period_end"], as_index=False).agg(so_per_game=("so_per_game", "mean"), hr_per_game=("hr_per_game", "mean"), 
    runs_per_game=("runs_per_game", "mean"))
agg["label"] = np.where(agg["period_start"] == agg["period_end"], agg["period_start"].astype(str), 
    agg["period_start"].astype(str) + "–" + agg["period_end"].astype(str).str[-2:])

x = agg["so_per_game"].to_numpy()
y = agg["hr_per_game"].to_numpy()
points = np.array([x, y]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

old_rgb = np.array([23, 50, 74]) / 255
red_rgb = np.array([217, 74, 58]) / 255
t = np.linspace(0, 1, len(segments))
segment_colors = old_rgb[None, :] * (1 - t[:, None]) + red_rgb[None, :] * t[:, None]
point_t = np.linspace(0, 1, len(agg))
point_colors = old_rgb[None, :] * (1 - point_t[:, None]) + red_rgb[None, :] * point_t[:, None]

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.10, 0.15, 0.82, 0.66], facecolor=BG)

ax.add_collection(LineCollection(segments, colors=segment_colors, linewidths=3.2, alpha=0.92, zorder=2))
ax.scatter(x, y, c=point_colors, s=52, edgecolor=BG, linewidth=0.9, zorder=3)

label_specs = {1900: ("above", 0.07), 
               1910: ("right", 0.16), 
               1955: ("above", 0.07), 
               1975: ("below", 0.07), 
               2000: ("above", 0.07), 
               2010: ("below", 0.07), 
               2025: ("below", 0.07)
}

for period, (direction, offset) in label_specs.items():
    row = agg.loc[agg["period_start"] == period].iloc[0]
    x0, y0 = row["so_per_game"], row["hr_per_game"]
    if direction == "above": tx, ty, ha, va = x0, y0 + offset, "center", "bottom"
    elif direction == "below": tx, ty, ha, va = x0, y0 - offset, "center", "top"
    elif direction == "left": tx, ty, ha, va = x0 - offset, y0, "right", "center"
    else: tx, ty, ha, va = x0 + offset, y0, "left", "center"
    ax.scatter(x0, y0, s=105, color=POINT, edgecolor=TEXT, linewidth=1.4, zorder=5)
    ax.text(tx, ty, f"{row['label']}\n{row['runs_per_game']:.1f} runs", ha=ha, va=va, fontsize=9, fontweight="bold", color=TEXT, zorder=6)

ax.set_xlim(x.min() - 0.8, x.max() + 1.0)
ax.set_ylim(max(0, y.min() - 0.2), y.max() + 0.35)
ax.set_xlabel("STRIKEOUTS PER GAME", fontsize=9, fontweight="bold", color=MUTED, labelpad=12)
ax.set_ylabel("HOME RUNS PER GAME", fontsize=9, fontweight="bold", color=MUTED, labelpad=12)
ax.tick_params(axis="both", colors=MUTED, labelsize=9, length=0)
ax.grid(color=GRID, linewidth=0.8, alpha=0.55)

for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  04/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "Baseball changed everything but the score", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each point is a five-year average of home runs and strikeouts per game; labels show average runs scored.", fontsize=10.5, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season records, 1900–2025 · Five-year averages", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=164, facecolor=BG)
plt.show()