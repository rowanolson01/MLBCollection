import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

INPUT = Path("_batting.csv")
OUTPUT = Path("stealsuccess.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
CREAM = "#F1EBDD"
RED = "#D94A3A"
GRID = "#AFC9D1"

df = pd.read_csv(INPUT, low_memory=False)

team_col = next(c for c in ["team", "batteam"] if c in df.columns)
pa_col = next(c for c in ["b_pa", "pa"] if c in df.columns)
sb_col = next(c for c in ["b_sb", "sb"] if c in df.columns)
cs_col = next(c for c in ["b_cs", "cs"] if c in df.columns)

df["season"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
df = df[df["season"].between(1910, 2025)].copy()
if "gametype" in df.columns: df = df[df["gametype"].eq("regular")].copy()

for col in [pa_col, sb_col, cs_col]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df = df.groupby(["season", team_col], as_index=False).agg(pa=(pa_col, "sum"), sb=(sb_col, "sum"), cs=(cs_col, "sum"))
df["sb_attempts"] = df["sb"] + df["cs"]
df["sb_success_pct"] = np.where(df["sb_attempts"].gt(0), df["sb"] / df["sb_attempts"] * 100, np.nan)
df["sb_attempts_per_100_pa"] = np.where(df["pa"].gt(0), df["sb_attempts"] / df["pa"] * 100, np.nan)

df["sb_success_pct"] = np.where(df["sb_attempts"].gt(0), df["sb"] / df["sb_attempts"] * 100, np.nan)
df = df[df["sb_success_pct"] < 100].copy()
df["sb_attempts_per_100_pa"] = np.where(df["pa"].gt(0), df["sb_attempts"] / df["pa"] * 100, np.nan)

df = df.dropna(subset=["sb_success_pct", "sb_attempts_per_100_pa"]).copy()
df = df[df["sb_attempts_per_100_pa"].ge(0.5)].copy()
df["decade"] = (df["season"] // 10) * 10

decades = sorted(df["decade"].unique())
old_rgb = np.array([23, 50, 74]) / 255
red_rgb = np.array([217, 74, 58]) / 255

def swarm_offsets(values, width=.34, bin_size=1.35):
    values = np.asarray(values, dtype=float)
    bins = np.floor(values / bin_size).astype(int)
    offsets = np.zeros(len(values))
    for b in np.unique(bins):
        idx = np.where(bins == b)[0]
        n = len(idx)
        if n < 2: continue
        order = np.arange(n)
        pattern = np.zeros(n)
        pattern[1::2] = np.ceil(order[1::2] / 2)
        pattern[2::2] = -np.ceil(order[2::2] / 2)
        max_abs = max(abs(pattern).max(), 1)
        offsets[idx] = pattern / max_abs * width
    return offsets

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.10, 0.15, 0.82, 0.67], facecolor=BG)

for i, decade in enumerate(decades):
    g = df[df["decade"].eq(decade)].sort_values("sb_success_pct").copy()
    t = i / max(1, len(decades) - 1)
    color = old_rgb * (1 - t) + red_rgb * t
    x = i + swarm_offsets(g["sb_success_pct"].to_numpy())
    ax.scatter(x, g["sb_success_pct"], s=18, color=color, edgecolor=BG, linewidth=.35, alpha=.72, zorder=3)
    median = g["sb_success_pct"].median()
    ax.scatter(i, median, s=72, color=CREAM, edgecolor=color, linewidth=1.3, zorder=5)

ax.set_xticks(range(len(decades)))
ax.set_xticklabels([f"{int(d)}s" for d in decades], fontsize=8.5, fontweight="bold", color=TEXT)
ax.set_ylim(20, 102)
ax.set_yticks(np.arange(20, 101, 10))
ax.tick_params(axis="x", length=0, pad=10)
ax.tick_params(axis="y", colors=MUTED, labelsize=9, length=0)
ax.set_ylabel("STOLEN-BASE SUCCESS RATE", fontsize=9, fontweight="bold", color=MUTED, labelpad=14)
ax.grid(axis="y", color=GRID, linewidth=.8, alpha=.45, zorder=0)

for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  10/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "Baseball learned when to run", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each dot is one team-season; modern teams steal successfully more often and cluster much closer together.", fontsize=11, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))
fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season batting records, 1910–2025 · Team-seasons with 0.5+ stolen-base attempts per 100 PA", fontsize=8.5, color=MUTED, 
    ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=300, facecolor=BG)
plt.show()