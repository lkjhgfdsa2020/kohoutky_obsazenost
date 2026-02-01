#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo

INPUT = "data/occupancy.csv"
OUT_DIR = "docs"
OUT_PNG = os.path.join(OUT_DIR, "heatmap.png")
OUT_HTML = os.path.join(OUT_DIR, "index.html")

def main():
    df = pd.read_csv(INPUT)

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts_utc", "pools_gym_current"])

    prague = ZoneInfo("Europe/Prague")
    df["ts_prague"] = df["ts_utc"].dt.tz_convert(prague)

    # 15-min bins in Prague time
    df["bin"] = df["ts_prague"].dt.floor("15min")
    df["weekday_num"] = df["bin"].dt.weekday  # Mon=0
    df["weekday"] = df["bin"].dt.day_name()
    df["time_hhmm"] = df["bin"].dt.strftime("%H:%M")
    df["occ"] = pd.to_numeric(df["pools_gym_current"], errors="coerce")
    df = df.dropna(subset=["occ"])

    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    times = pd.date_range("2000-01-01 06:00", "2000-01-01 21:45", freq="15min").strftime("%H:%M").tolist()

    pivot = (
        df.groupby(["weekday_num","time_hhmm"])["occ"].mean()
          .unstack("time_hhmm")
          .reindex(range(7))
          .reindex(columns=times)
    )

    os.makedirs(OUT_DIR, exist_ok=True)

    # Heatmap
    fig, ax = plt.subplots(figsize=(14, 4.8))
    im = ax.imshow(pivot.values, aspect="auto")  # default colormap (low=dark)
    ax.set_yticks(range(7))
    ax.set_yticklabels(weekday_order)

    xticks = list(range(0, len(times), 4))  # hourly labels
    ax.set_xticks(xticks)
    ax.set_xticklabels([times[i] for i in xticks], rotation=45, ha="right")

    ax.set_title("Average pools+gym occupancy — 15-minute bins (Prague time)")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Average people (pools_gym_current)")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=200)
    plt.close(fig)

    # Simple HTML page for GitHub Pages
    updated = pd.Timestamp.now(tz=prague).strftime("%Y-%m-%d %H:%M %Z")
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Aquapark occupancy heatmap</title></head>
<body style="font-family: system-ui; padding: 20px;">
  <h2>Aquapark occupancy heatmap</h2>
  <p>Updated: {updated}</p>
  <img src="heatmap.png" style="max-width: 100%; height: auto;" />
</body>
</html>
""")

if __name__ == "__main__":
    main()
