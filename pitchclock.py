import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path
from scipy.interpolate import make_interp_spline

GAMEINFO = Path("_gameinfo.csv")
BATTING = Path("_batting.csv")
OUTPUT = Path("pitchclock.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
BAR = "#F1EBDD"
RED = "#D94A3A"
YELLOW = "#E8C56A"
GRID = "#AFC9D1"
CENTER = "#D7E1DF"

games = pd.read_csv(GAMEINFO, low_memory=False)
bat = pd.read_csv(BATTING, low_memory=False)

time_col = next(c for c in ["timeofgame", "time_of_game", "minutes", "game_minutes", "duration"] if c in games.columns)
pa_col = next(c for c in ["b_pa", "pa"] if c in bat.columns)

games["season"] = pd.to_numeric(games["date"].astype(str).str[:4], errors="coerce")
bat["season"] = pd.to_numeric(bat["date"].astype(str).str[:4], errors="coerce")

games = games[games["season"].between(1897, 2025)].copy()
bat = bat[bat["season"].between(1897, 2025)].copy()

if "gametype" in games.columns: games = games[games["gametype"].eq("regular")].copy()
if "gametype" in bat.columns: bat = bat[bat["gametype"].eq("regular")].copy()

games[time_col] = pd.to_numeric(games[time_col], errors="coerce")
bat[pa_col] = pd.to_numeric(bat[pa_col], errors="coerce").fillna(0)

pa_game = bat.groupby("gid", as_index=False)[pa_col].sum().rename(columns={pa_col:"plate_appearances"})
game = games[["gid", "season", time_col]].drop_duplicates("gid").merge(pa_game, on="gid", how="inner")
game = game[game[time_col].gt(0) & game["plate_appearances"].gt(0)].copy()
game["hours"] = game[time_col] / 60

df = game.groupby("season", as_index=False).agg(plate_appearances=("plate_appearances", "sum"), hours=("hours", "sum"))
df["avg_pa_per_hour"] = df["plate_appearances"] / df["hours"]
df = df[df["avg_pa_per_hour"].notna()].sort_values("season").reset_index(drop=True)

years = df["season"].to_numpy()
pace = df["avg_pa_per_hour"].to_numpy()

n = len(df)
theta = np.linspace(0.015, 2 * np.pi - 0.015, n)
width = (2 * np.pi / n) * 0.78

pace_min = pace.min()
pace_max = pace.max()
slowness = (pace_max - pace) / (pace_max - pace_min)

inner_radius = 2.75
bar_min = 0.7
bar_max = 5.8
heights = bar_min + slowness * (bar_max - bar_min)

df["decade"] = (df["season"] // 10) * 10
decades = df.groupby("decade", as_index=False).agg(avg_pace=("avg_pa_per_hour", "mean"), mid_year=("season", "mean"))

row_2025 = df.loc[df["season"].eq(2025), ["season", "avg_pa_per_hour"]].iloc[0]
trend_years = np.append(decades["mid_year"].to_numpy(), row_2025["season"])
trend_pace = np.append(decades["avg_pace"].to_numpy(), row_2025["avg_pa_per_hour"])

trend_theta = np.interp(trend_years, years, theta)
trend_slowness = (pace_max - trend_pace) / (pace_max - pace_min)
trend_radius = 3.45 + trend_slowness * 2.7

theta_smooth = np.linspace(trend_theta.min(), trend_theta.max(), 600)
radius_smooth = make_interp_spline(trend_theta, trend_radius, k=3)(theta_smooth)

fig = plt.figure(figsize=(12, 12), facecolor=BG)
ax = fig.add_axes([0.08, 0.11, 0.84, 0.73], projection="polar", facecolor=BG)

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_ylim(0, inner_radius + bar_max + 1.4)
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.spines["polar"].set_visible(False)

for r in [inner_radius, inner_radius + 2, inner_radius + 4]: ax.plot(np.linspace(0, 2 * np.pi, 500), np.full(500, r), color=GRID, linewidth=0.8, alpha=0.65, zorder=0)

mask_old = years < 2023
mask_new = years >= 2023

ax.bar(theta[mask_old], heights[mask_old], width=width, bottom=inner_radius, color=BAR, edgecolor=BG, linewidth=0.6, zorder=2)
ax.bar(theta[mask_new], heights[mask_new], width=width, bottom=inner_radius, color=RED, edgecolor=BG, linewidth=0.6, zorder=3)

ax.plot(theta_smooth, radius_smooth, color=YELLOW, linewidth=3.4, solid_capstyle="round", zorder=5)
ax.scatter(trend_theta, trend_radius, s=30, color=YELLOW, edgecolor=TEXT, linewidth=1.1, zorder=6)

label_radius = inner_radius + bar_max + 0.42

for year in range(1900, 2030, 10):
    if year > years.max(): continue
    idx = np.abs(years - year).argmin()
    angle = theta[idx]
    rotation = np.degrees(-angle)
    ax.text(angle, label_radius, str(year), ha="center", va="center", fontsize=8.5, fontweight="bold", color=TEXT, rotation=rotation, rotation_mode="anchor", zorder=7)

idx_2023 = np.where(years == 2023)[0][0]
idx_2025 = np.where(years == 2025)[0][0]

ax.scatter(theta[idx_2025], trend_radius[-1], s=90, color=RED, edgecolor=BAR, linewidth=1.8, zorder=8)

callout_theta = np.deg2rad(10)
callout_radius = inner_radius + 3

ax.annotate("2023  •  PITCH CLOCK ERA", xy=(theta[idx_2025], inner_radius + heights[idx_2025] - 0.6), xytext=(callout_theta, callout_radius), ha="left", va="center", 
    fontsize=10.5, fontweight="bold", color=RED, arrowprops=dict(arrowstyle="-|>", color=RED, linewidth=1.8, shrinkA=8, shrinkB=4), zorder=10)

center = Circle((0.5, 0.5), 0.125, transform=ax.transAxes, facecolor=CENTER, edgecolor="none", zorder=20)
ax.add_patch(center)

fig.text(0.08, 0.955, "MLB COLLECTION  ·  01/10", fontsize=10, fontweight="bold", color=RED, ha="left")
fig.text(0.08, 0.905, "The pitch clock erased decades of baseball slowdown", fontsize=25, fontweight="bold", color=TEXT, ha="left")
fig.text(0.08, 0.870, "Each bar is one MLB season. Taller bars mean fewer plate appearances per hour; the yellow curve shows decade-average pace.", 
    fontsize=11.2, color=MUTED, ha="left")
fig.lines.append(plt.Line2D([0.08, 0.92], [0.842, 0.842], transform=fig.transFigure, color=TEXT, linewidth=1.2))

fig.text(0.08, 0.045, "Source: Retrosheet · MLB game records, 1897–2025", fontsize=8.5, color=MUTED, ha="left")
fig.text(0.92, 0.045, "Analysis + design: Rowan Olson", fontsize=8.5, fontweight="bold", color=TEXT, ha="right")

plt.savefig(OUTPUT, dpi=164, facecolor=BG)
plt.show()