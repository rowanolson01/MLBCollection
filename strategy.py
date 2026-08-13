import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from pathlib import Path

INPUT = Path("_batting.csv")
OUTPUT = Path("strategy.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
GRID = "#AFC9D1"

COLORS = {
    "home runs": "#A7433F",
    "sacrifice hits": "#E8DFCB",
    "stolen-base attempts": "#66506A"
}

LABELS = {
    "home runs": "HOME RUNS",
    "sacrifice hits": "SACRIFICE HITS",
    "stolen-base attempts": "STOLEN-BASE ATTEMPTS"
}

df = pd.read_csv(INPUT, low_memory=False)
df["season"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
df = df[df["season"].between(1900, 2025)].copy()
if "gametype" in df.columns: df = df[df["gametype"].eq("regular")].copy()

for col in ["b_pa", "b_hr", "b_sh", "b_sb", "b_cs"]: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

season = df.groupby("season", as_index=False).agg(pa=("b_pa", "sum"), hr=("b_hr", "sum"), sh=("b_sh", "sum"), sb=("b_sb", "sum"), cs=("b_cs", "sum"))
season = season[season["pa"] > 0].copy()

season["home runs"] = season["hr"] / season["pa"] * 100
season["sacrifice hits"] = season["sh"] / season["pa"] * 100
season["stolen-base attempts"] = (season["sb"] + season["cs"]) / season["pa"] * 100
season["decade"] = season["season"] // 10 * 10

decade = season.groupby("decade", as_index=False).agg({"home runs": "mean", "sacrifice hits": "mean", "stolen-base attempts": "mean"})
decade = decade[decade["decade"].between(1900, 2020)].copy()

long = decade.melt(id_vars="decade", var_name="strategy", value_name="rate")
long["rank"] = long.groupby("decade")["rate"].rank(method="first", ascending=False)

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.10, 0.17, 0.80, 0.63], facecolor=BG)

for strategy in COLORS:
    x = long.loc[long["strategy"].eq(strategy), "decade"].to_numpy()
    y = long.loc[long["strategy"].eq(strategy), "rank"].to_numpy()
    xs = np.linspace(x.min(), x.max(), 700)
    ys = PchipInterpolator(x, y)(xs)
    ax.plot(xs, ys, color=COLORS[strategy], linewidth=4, zorder=3)
    ax.scatter(x, y, s=115, color=COLORS[strategy], edgecolor=BG, linewidth=1.5, zorder=4)

for decade_year in decade["decade"]: ax.axvline(decade_year, color=GRID, linewidth=0.7, alpha=0.35, zorder=0)

first_decade = long[long["decade"].eq(long["decade"].min())]

for _, row in first_decade.iterrows():
    ax.text(row["decade"] + 1.5, row["rank"] - 0.06, LABELS[row["strategy"]], ha="left", va="bottom", fontsize=9, fontweight="bold", color=COLORS[row["strategy"]], zorder=10)

ax.set_xlim(1895, 2025)
ax.set_ylim(3.45, 0.55)
ax.set_xticks(decade["decade"])
ax.set_xticklabels([f"{int(x)}s" for x in decade["decade"]], rotation=45, ha="right")
ax.set_yticks([1, 2, 3])
ax.set_yticklabels(["1ST", "2ND", "3RD"])
ax.tick_params(axis="both", colors=MUTED, labelsize=9, length=0)
ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.45)

for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  07/10", fontsize=10, fontweight="bold", color="#D94A3A", ha="left")
fig.text(0.08, 0.905, "The bunt died. Small ball didn't", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each decade ranks three offensive strategies by events per 100 plate appearances.", fontsize=11, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season batting records, 1900–2025", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=300, facecolor=BG)
plt.show()