import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

BATTING = Path("_batting.csv")
PITCHING = Path("_pitching.csv")
OUTPUT = Path("teamidentity.png")

BG = "#8FB7C4"
TEXT = "#17324A"
MUTED = "#4E6978"
RED = "#D94A3A"
GRID = "#AFC9D1"

COLORS = {1:"#376A78", 
          2:"#B56B58", 
          3:"#C7473B", 
          4:"#986C2C", 
          5:"#795B83", 
          6:"#315E87"
}

NAMES = {1:"Run Prevention", 
         2:"Pitching Vulnerability", 
         3:"Power + Command", 
         4:"Small Ball", 
         5:"High-Variance Power", 
         6:"Modern Power"
}

DESCRIPTIONS = {1:"Suppresses homers and walks", 
                2:"More walks and homers allowed, fewer Ks", 
                3:"Elite power with strikeout pitching", 
                4:"More steals and sacrifices, fewer homers", 
                5:"Power paired with volatile run prevention", 
                6:"Power-heavy with little small-ball play"
}

LABELS = {1:(1.85,-2.10), 
          2:(-2.15,2.15), 
          3:(3.30,-1.63), 
          4:(-2.70,-0.52), 
          5:(0.90,3.62), 
          6:(1.80,2.18)
}

bat = pd.read_csv(BATTING, low_memory=False)
pit = pd.read_csv(PITCHING, low_memory=False)

bat["season"] = pd.to_numeric(bat["date"].astype(str).str[:4], errors="coerce")
pit["season"] = pd.to_numeric(pit["date"].astype(str).str[:4], errors="coerce")
bat = bat[bat["season"].between(2015,2025)].copy()
pit = pit[pit["season"].between(2015,2025)].copy()

if "gametype" in bat.columns: bat = bat[bat["gametype"].eq("regular")].copy()
if "gametype" in pit.columns: pit = pit[pit["gametype"].eq("regular")].copy()

for col in ["b_pa","b_ab","b_h","b_hr","b_k","b_sb","b_cs","b_sh"]: bat[col] = pd.to_numeric(bat[col], errors="coerce").fillna(0)
for col in ["p_k","p_w","p_hr","p_ipouts"]: pit[col] = pd.to_numeric(pit[col], errors="coerce").fillna(0)

bat = bat.groupby(["season","team"], as_index=False).agg(pa=("b_pa","sum"), ab=("b_ab","sum"), hits=("b_h","sum"), hr=("b_hr","sum"), batter_so=("b_k","sum"), 
    sb=("b_sb","sum"), cs=("b_cs","sum"), sh=("b_sh","sum"))
bat["hr_per_100_pa"] = bat["hr"] / bat["pa"] * 100
bat["hits_per_100_ab"] = bat["hits"] / bat["ab"] * 100
bat["so_per_100_pa"] = bat["batter_so"] / bat["pa"] * 100
bat["sb_attempts_per_100_pa"] = (bat["sb"] + bat["cs"]) / bat["pa"] * 100
bat["sh_per_100_pa"] = bat["sh"] / bat["pa"] * 100
bat = bat.rename(columns={"team":"franchise"})

pit = pit.groupby(["season","team"], as_index=False).agg(pitcher_so=("p_k","sum"), bb=("p_w","sum"), hr_allowed=("p_hr","sum"), outs=("p_ipouts","sum"))
pit["innings"] = pit["outs"] / 3
pit["so_per_9"] = pit["pitcher_so"] / pit["innings"] * 9
pit["bb_per_9"] = pit["bb"] / pit["innings"] * 9
pit["hr_allowed_per_9"] = pit["hr_allowed"] / pit["innings"] * 9
pit = pit.rename(columns={"team":"franchise"})

df = bat.merge(pit[["season","franchise","so_per_9","bb_per_9","hr_allowed_per_9"]], on=["season","franchise"], how="inner")

franchise_map = {"ANA":"LAA","FLA":"MIA","TBD":"TBA","MON":"WAS"}
df["franchise"] = df["franchise"].replace(franchise_map)

features = ["hr_per_100_pa","hits_per_100_ab","so_per_100_pa","sb_attempts_per_100_pa","sh_per_100_pa","so_per_9","bb_per_9","hr_allowed_per_9"]

for feature in features: df[f"z_{feature}"] = df.groupby("season")[feature].transform(lambda x:(x-x.mean())/x.std(ddof=0))

z_features = [f"z_{c}" for c in features]
profiles = df.groupby("franchise", as_index=False)[z_features].mean()
profiles.columns = ["franchise"] + features
profiles = profiles.dropna(subset=features).copy()

X = StandardScaler().fit_transform(profiles[features])
pca = PCA(n_components=2)
coords = pca.fit_transform(X)

plot_df = profiles[["franchise"]].copy()
plot_df["PC1"] = coords[:,0]
plot_df["PC2"] = coords[:,1]

pc1_var = pca.explained_variance_ratio_[0]
pc2_var = pca.explained_variance_ratio_[1]

model = KMeans(n_clusters=6, random_state=42, n_init=50)
plot_df["cluster"] = model.fit_predict(plot_df[["PC1","PC2"]]) + 1

def add_ellipse(ax,x,y,color):
    points = np.column_stack([x,y])
    center = points.mean(axis=0)
    if len(points) == 2:
        dx,dy = points[1]-points[0]
        width = np.hypot(dx,dy)+1.1
        height = 1.15
        angle = np.degrees(np.arctan2(dy,dx))
    else:
        cov = np.cov(points.T)
        values,vectors = np.linalg.eigh(cov)
        order = values.argsort()[::-1]
        values,vectors = values[order],vectors[:,order]
        width,height = 2*1.55*np.sqrt(values)
        angle = np.degrees(np.arctan2(vectors[1,0],vectors[0,0]))
        width += 0.45
        height += 0.35
    ax.add_patch(Ellipse(center,width,height,angle=angle,facecolor=color,edgecolor=color,linewidth=1.4,alpha=0.14,zorder=1))

fig = plt.figure(figsize=(12,12),facecolor=BG)
ax = fig.add_axes([0.10,0.15,0.82,0.67],facecolor=BG)

for cluster in sorted(plot_df["cluster"].unique()):
    group = plot_df[plot_df["cluster"].eq(cluster)]
    add_ellipse(ax,group["PC1"].to_numpy(),group["PC2"].to_numpy(),COLORS[cluster])
    ax.scatter(group["PC1"],group["PC2"],s=62,color=COLORS[cluster],edgecolor=BG,linewidth=1.0,alpha=0.82,zorder=3)

for _,row in plot_df.iterrows(): ax.text(row["PC1"]+0.06,row["PC2"]+0.05,row["franchise"],ha="left",va="bottom",fontsize=7.5,fontweight="bold",color=TEXT,alpha=0.82,zorder=7)

for cluster,(x,y) in LABELS.items():
    ax.text(x,y,NAMES[cluster],ha="center",va="bottom",fontsize=10.5,fontweight="bold",color=COLORS[cluster],zorder=8)
    ax.text(x,y-0.08,DESCRIPTIONS[cluster],ha="center",va="top",fontsize=7.1,color=COLORS[cluster],zorder=8)

ax.axhline(0,color=GRID,linewidth=0.9,alpha=0.55,zorder=0)
ax.axvline(0,color=GRID,linewidth=0.9,alpha=0.55,zorder=0)
ax.grid(color=GRID,linewidth=0.8,alpha=0.35,zorder=0)

ax.set_xlim(-3.35,4.25)
ax.set_ylim(-3.0,4.15)
ax.set_xlabel(f"PC1 · POWER, PITCHING STRIKEOUTS & CONTROL ({pc1_var:.1%})",fontsize=9,fontweight="bold",color=MUTED,labelpad=14)
ax.set_ylabel(f"PC2 · LONG-BALL EXPOSURE VS SMALL-BALL PLAY ({pc2_var:.1%})",fontsize=9,fontweight="bold",color=MUTED,labelpad=14)
ax.tick_params(axis="both",colors=MUTED,labelsize=9,length=0)

for spine in ax.spines.values(): spine.set_visible(False)

fig.text(0.08,0.955,"MLB COLLECTION  ·  09/10",fontsize=10,fontweight="bold",color=RED,ha="left")
fig.text(0.08,0.905,"There is more than one way to build a baseball team",fontsize=25,fontweight="bold",color=TEXT,ha="left")
fig.text(0.08,0.870,"Franchise profiles from 2015–2025 separate into six statistical archetypes across eight standardized measures.",fontsize=11,color=MUTED,ha="left")
fig.lines.append(plt.Line2D([0.08,0.92],[0.842,0.842],transform=fig.transFigure,color=TEXT,linewidth=1.2))
fig.text(0.08,0.045,"Source: Retrosheet · MLB regular-season team records, 2015–2025",fontsize=8.5,color=MUTED,ha="left")
fig.text(0.92,0.045,"Analysis + design: Rowan Olson",fontsize=8.5,fontweight="bold",color=TEXT,ha="right")

plt.savefig(OUTPUT,dpi=300,facecolor=BG)
plt.show()