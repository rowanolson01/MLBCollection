import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

INPUT = Path("_batting.csv")
OUTPUT = Path("winningrecipe.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
CREAM = "#F1EBDD"
RED = "#D94A3A"
GRID = "#AFC9D1"

df = pd.read_csv(INPUT, low_memory=False)

df["season"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
df = df[df["season"].between(1900, 2025)].copy()
if "gametype" in df.columns: df = df[df["gametype"].eq("regular")].copy()

for col in ["b_pa", "b_hr"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df = df.groupby(["season", "team"], as_index=False).agg(pa=("b_pa", "sum"), hr=("b_hr", "sum"))
df = df[df["pa"].gt(0)].copy()
df["hr_per_100_pa"] = df["hr"] / df["pa"] * 100
df["period_start"] = ((df["season"] - 1900) // 5) * 5 + 1900

summary = df.groupby("period_start")["hr_per_100_pa"].quantile([0.10, 0.50, 0.90]).unstack().reset_index()
summary.columns = ["period_start", "p10", "median", "p90"]
summary["period_end"] = np.minimum(summary["period_start"] + 4, 2025)
summary["label"] = summary.apply(lambda r: f"{int(r['period_start'])}–{str(int(r['period_end']))[-2:]}", axis=1)
summary = summary.sort_values("period_start").reset_index(drop=True)

y = np.arange(len(summary))

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.18, 0.15, 0.72, 0.67], facecolor=BG)

for i, row in summary.iterrows():
    t = i / max(1, len(summary) - 1)
    color = tuple(np.array([23, 50, 74]) / 255 * (1 - t) + np.array([217, 74, 58]) / 255 * t)
    ax.plot([row["p10"], row["p90"]], [i, i], color=color, linewidth=4, solid_capstyle="round", zorder=2)
    ax.scatter([row["p10"], row["p90"]], [i, i], s=48, color=color, edgecolor=BG, linewidth=0.8, zorder=3)
    ax.scatter(row["median"], i, s=105, color=CREAM, edgecolor=color, linewidth=1.5, zorder=4)

ax.set_yticks(y)
ax.set_yticklabels(summary["label"], fontsize=8.5, fontweight="bold", color=TEXT)
ax.invert_yaxis()
ax.set_xlim(0, summary["p90"].max() + 0.35)
ax.set_xlabel("HOME RUNS PER 100 PLATE APPEARANCES", fontsize=9, fontweight="bold", color=MUTED, labelpad=14)
ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
ax.tick_params(axis="y", length=0, pad=10)
ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.45, zorder=0)

for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  08/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "The long ball swallowed the league", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each five-year range spans the 10th to 90th percentile of team home-run rates; the dot marks the median.", fontsize=11, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season team records, 1900–2025", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=300, facecolor=BG)
plt.show()