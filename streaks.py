import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.interpolate import make_interp_spline

INPUT = Path("_gameinfo.csv")
OUTPUT = Path("streaks.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
RED = "#D94A3A"
GRID = "#AFC9D1"

df = pd.read_csv(INPUT, low_memory=False)
df = df[df["gametype"] == "regular"].copy()
df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")

home = df[["date", "season", "hometeam"]].rename(columns={"hometeam": "team"})
away = df[["date", "season", "visteam"]].rename(columns={"visteam": "team"})
games = pd.concat([home, away], ignore_index=True).drop_duplicates(["team", "season", "date"]).sort_values(["season", "team", "date"]).reset_index(drop=True)

rows = []

for season in range(1960, 2026):
    season_df = games[games["season"] == season]
    stretch_lengths = []

    for _, team_df in season_df.groupby("team"):
        dates = team_df["date"].drop_duplicates().sort_values().reset_index(drop=True)
        gaps = dates.diff().dt.days
        groups = gaps.ne(1).cumsum()
        stretch_lengths.extend(dates.groupby(groups).size().tolist())

    rows.append({
        "season": season,
        "max_stretch": max(stretch_lengths),
        "avg_stretch": sum(stretch_lengths) / len(stretch_lengths)
    })

summary = pd.DataFrame(rows)

x = summary["season"].to_numpy()
max_y = summary["max_stretch"].to_numpy()
avg_y = summary["avg_stretch"].to_numpy()

x_smooth = np.linspace(x.min(), x.max(), 700)
max_smooth = make_interp_spline(x, max_y, k=2)(x_smooth)
avg_smooth = make_interp_spline(x, avg_y, k=2)(x_smooth)

trend_coef = np.polyfit(x, max_y, 1)
max_trend = np.polyval(trend_coef, x_smooth)

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.09, 0.16, 0.83, 0.64], facecolor=BG)

ax.plot(x_smooth, max_trend, color=RED, linewidth=5.5, alpha=0.18, zorder=1)
ax.plot(x_smooth, max_smooth, color=RED, linewidth=2.7, zorder=3)
ax.plot(x_smooth, avg_smooth, color=TEXT, linewidth=2.7, zorder=3)

ax.scatter(x, max_y, color=RED, s=16, edgecolor=BG, linewidth=0.5, zorder=4)
ax.scatter(x, avg_y, color=TEXT, s=14, edgecolor=BG, linewidth=0.5, zorder=4)

ax.set_xlim(1960, 2025)
ax.set_ylim(0, 54)
ax.set_xticks(range(1960, 2030, 10))
ax.set_yticks(range(0, 60, 10))
ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
ax.tick_params(axis="y", colors=MUTED, labelsize=9, length=0)
ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.65)
ax.grid(axis="x", visible=False)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_ylabel("consecutive game days", fontsize=9, color=MUTED, labelpad=10)

record = summary.loc[summary["max_stretch"].idxmax()]

ax.text(
    record["season"],
    record["max_stretch"] + 2.1,
    f"{int(record['max_stretch'])} straight days",
    ha="center",
    va="bottom",
    fontsize=10,
    fontweight="bold",
    color=RED
)

max_handle = plt.Line2D([0], [0], color=RED, linewidth=3, marker="o", markersize=5, label="Longest uninterrupted stretch")
avg_handle = plt.Line2D([0], [0], color=TEXT, linewidth=3, marker="o", markersize=5, label="Average uninterrupted stretch")

legend = ax.legend(handles=[max_handle, avg_handle], loc="upper right", frameon=False, fontsize=9, labelcolor=TEXT, handlelength=2.8)

for text in legend.get_texts():
    text.set_fontweight("bold")

fig.text(0.08, 0.955, "MLB COLLECTION  ·  02/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "Baseball killed the marathon", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Extreme stretches have collapsed since the 1960s, while the typical run between off-days barely moved.", fontsize=11.2, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB regular-season schedules, 1960–2025", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=164, facecolor=BG)
plt.show()