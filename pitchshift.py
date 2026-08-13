import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle
from pathlib import Path as FilePath

INPUT = FilePath("_pitching.csv")
OUTPUT = FilePath("pitchshift.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
STARTER = "#F1EBDD"
RELIEF1 = "#E8C56A"
RELIEF2 = "#D98B5F"
RELIEF3 = "#D94A3A"
RELIEF4 = "#8A3D4C"
GRID = "#AFC9D1"

ROLES = ["Starter", "1st reliever", "2nd reliever", "3rd reliever", "4th+ relievers"]
COLORS = [STARTER, RELIEF1, RELIEF2, RELIEF3, RELIEF4]
ERAS = [1900, 1925, 1950, 1975, 2000, 2025]
WINDOW = 2

df = pd.read_csv(INPUT, low_memory=False)
df = df[df["gametype"] == "regular"].copy()
df["season"] = df["date"].astype(str).str[:4].astype(int)
df = df[df["season"].between(1898, 2025)].copy()
df["p_ipouts"] = pd.to_numeric(df["p_ipouts"], errors="coerce").fillna(0)
df["p_seq"] = pd.to_numeric(df["p_seq"], errors="coerce")
df["role"] = np.select([df["p_seq"].eq(1), df["p_seq"].eq(2), df["p_seq"].eq(3), df["p_seq"].eq(4), df["p_seq"].ge(5)], ROLES, default="Other")
df = df[df["role"] != "Other"].copy()

era_rows = []

for era in ERAS:
    x = df[df["season"].between(era - WINDOW, era + WINDOW)]
    totals = x.groupby("role")["p_ipouts"].sum()
    total = totals.sum()
    row = {"era": era}
    for role in ROLES: row[role] = totals.get(role, 0) / total * 100
    era_rows.append(row)

era = pd.DataFrame(era_rows)

xpos = np.arange(len(ERAS)) * 2.2
station_width = 0.18
chart_bottom = 8
chart_height = 82
gap = 0.65

def station_bounds(row):
    values = np.array([row[role] for role in ROLES])
    usable = chart_height - gap * (len(ROLES) - 1)
    heights = values / values.sum() * usable
    bottoms = []
    y = chart_bottom
    for h in heights:
        bottoms.append(y)
        y += h + gap
    return np.array(bottoms), heights

bounds = [station_bounds(row) for _, row in era.iterrows()]

def ribbon(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha=0.96):
    c = (x1 - x0) * 0.42
    verts = [(x0, y0a), (x0 + c, y0a), (x1 - c, y1a), (x1, y1a), (x1, y1b), (x1 - c, y1b), (x0 + c, y0b), (x0, y0b), (x0, y0a)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=2))

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.08, 0.15, 0.84, 0.66], facecolor=BG)

for i in range(len(ERAS) - 1):
    bottoms0, heights0 = bounds[i]
    bottoms1, heights1 = bounds[i + 1]
    for j, color in enumerate(COLORS): ribbon(ax, xpos[i] + station_width / 2, xpos[i + 1] - station_width / 2, bottoms0[j], bottoms0[j] + heights0[j], bottoms1[j], 
        bottoms1[j] + heights1[j], color)

for i, year in enumerate(ERAS):
    bottoms, heights = bounds[i]
    for j, color in enumerate(COLORS): ax.add_patch(Rectangle((xpos[i] - station_width / 2, bottoms[j]), station_width, heights[j], facecolor=color, edgecolor=BG, 
        linewidth=0.8, zorder=4))
    ax.text(xpos[i], chart_bottom - 4.2, str(year), ha="center", va="top", fontsize=10, fontweight="bold", color=TEXT)

for y in [20, 40, 60, 80]: ax.axhline(y, color=GRID, linewidth=0.7, alpha=0.45, zorder=0)

ax.set_xlim(xpos[0] - 0.8, xpos[-1] + 0.8)
ax.set_ylim(0, 100)
ax.set_xticks([])
ax.set_yticks([])

for spine in ax.spines.values(): spine.set_visible(False)

right_bottoms, right_heights = bounds[-1]

for j, role in enumerate(ROLES):
    if right_heights[j] > 3: ax.text(xpos[-1] + 0.22, right_bottoms[j] + right_heights[j] / 2, role, ha="left", va="center", fontsize=9, fontweight="bold", color=TEXT)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  03/10", fontsize=10, fontweight="bold", color=RELIEF3, ha="left")
fig.text(0.08, 0.905, "Baseball broke one job into five", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Ribbon width shows each pitcher’s share of innings, tracing how the starter’s workload steadily splintered across the bullpen.", fontsize=11.2, 
    color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season pitching records, 1900–2025", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=164, facecolor=BG)
plt.show()