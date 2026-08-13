import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from scipy.ndimage import gaussian_filter1d
from pathlib import Path
import re

INPUT = Path("_teamstats.csv")
OUTPUT = Path("extras.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
CREAM = "#F1EBDD"
RED = "#D94A3A"
DARK_RED = "#8F363A"
NAVY = "#17324A"

df = pd.read_csv(INPUT, low_memory=False)
df["season"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
df = df[df["season"].between(1900, 2025)].copy()
if "gametype" in df.columns: df = df[df["gametype"].eq("regular")].copy()

def inning_number(name):
    low = name.lower()
    for pattern in [r"(?:^|_)(?:inn|inning|score|runs?)_?(\d{1,2})(?:$|_)", r"(?:^|_)(\d{1,2})(?:st|nd|rd|th)?_?inning(?:$|_)", r"(?:^|_)inning_?(\d{1,2})(?:$|_)"]:
        match = re.search(pattern, low)
        if match: return int(match.group(1))
    return None

inning_cols = {col: inning_number(col) for col in df.columns}
inning_cols = {col: inning for col, inning in inning_cols.items() if inning is not None and inning >= 10}
if not inning_cols: raise ValueError("No extra-inning scoring columns detected in _teamstats.csv.")

rows = []
for col, inning in inning_cols.items():
    x = df[["season", col]].copy()
    x["runs"] = pd.to_numeric(x[col], errors="coerce")
    x["inning"] = inning
    rows.append(x[["season", "inning", "runs"]])

extras = pd.concat(rows, ignore_index=True).dropna(subset=["runs"])
season = extras.groupby("season", as_index=False).agg(avg_runs=("runs", "mean"), team_innings=("runs", "size"))
season = season[season["team_innings"] >= 20].copy()

years = np.arange(1900, 2026)
plot = pd.DataFrame({"season": years}).merge(season, on="season", how="left")
plot["avg_runs_fill"] = plot["avg_runs"].interpolate(limit_direction="both")

pre = season[season["season"].between(1900, 2019)]["avg_runs"].mean()
post = season[season["season"].between(2020, 2025)]["avg_runs"].mean()

cmap = LinearSegmentedColormap.from_list("extras", [NAVY, DARK_RED])
norm = Normalize(vmin=season["avg_runs"].quantile(0.02), vmax=season["avg_runs"].quantile(0.98))

raw = plot["avg_runs_fill"].to_numpy()
smooth = gaussian_filter1d(raw, sigma=2.2)
low, high = np.nanpercentile(smooth, [2, 98])
height = 0.18 + 0.72 * ((smooth - low) / (high - low))
height = np.clip(height, 0.18, 0.90)
modern = plot["season"] >= 2020
height[modern] = 0.18 + 0.72 * ((raw[modern] - low) / (high - low))
height = np.clip(height, 0.18, 0.96)

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.08, 0.25, 0.84, 0.48], facecolor=BG)

for i, row in plot.iterrows():
    year, h, value = int(row["season"]), height[i], row["avg_runs"]
    color = BG if pd.isna(value) else cmap(norm(value))
    ax.fill_between([year - 0.5, year + 0.5], [-h, -h], [h, h], color=color, linewidth=0, zorder=2)

ax.axvline(2019.5, color=CREAM, linewidth=2, zorder=6)
ax.text(2019, 1.03, "AUTOMATIC RUNNER\nINTRODUCED · 2020", ha="right", va="bottom", fontsize=9, fontweight="bold", color=CREAM)

ax.text(1960, 0.06, f"{pre:.2f}", ha="center", va="center", fontsize=34, fontweight="bold", color=CREAM, zorder=7)
ax.text(1960, -0.10, "RUNS PER EXTRA TEAM-INNING\nBEFORE 2020", ha="center", va="center", fontsize=8, fontweight="bold", color=CREAM, zorder=7)

ax.text(2031.0, 0.06, f"{post:.2f}", ha="center", va="center", fontsize=20, fontweight="bold", color=TEXT, clip_on=False, zorder=7)
ax.text(2031.0, -0.10, "2020–25", ha="center", va="center", fontsize=8, fontweight="bold", color=TEXT, clip_on=False, zorder=7)

ax.set_xlim(1899.5, 2025.5)
ax.set_ylim(-1.08, 1.08)
ax.set_xticks([1900, 1925, 1950, 1975, 2000, 2020, 2025])
ax.set_yticks([])
ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  06/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "Extra innings became a different game", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each stripe is one season; height and color both encode runs scored per extra team-inning.", fontsize=11, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))
fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season team scoring records, 1900–2025", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=300, facecolor=BG)
plt.show()