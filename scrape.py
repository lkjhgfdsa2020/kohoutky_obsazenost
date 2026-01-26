#!/usr/bin/env python3
import csv
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

URL = "https://aquapark.starez.cz/"

TARGETS = {
    "BAZÉNY A POSILOVNA": "pools_gym",
    "FINSKÁ SAUNA": "finnish_sauna",
}

def within_opening_hours() -> bool:
    now_prague = datetime.now(ZoneInfo("Europe/Prague"))
    return 6 <= now_prague.hour < 22

def parse_ratio(text: str):
    m = re.search(r"(\d+)\s*/\s*(\d+)", text)
    return (int(m.group(1)), int(m.group(2))) if m else None

def fetch_counts():
    r = requests.get(
        URL,
        headers={"User-Agent": "occupancy-stats-bot/1.0"},
        timeout=20,
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    results = {}

    for label, key in TARGETS.items():
        p = soup.find(lambda tag: tag.name == "p" and tag.get_text(strip=True) == label)
        ratio = None
        if p and p.parent:
            ratio = parse_ratio(p.parent.get_text(" ", strip=True))
        results[key] = ratio

    return results

def append_csv(path: str, ts_utc: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow([
                "ts_utc",
                "pools_gym_current", "pools_gym_capacity",
                "finnish_sauna_current", "finnish_sauna_capacity",
            ])

        pg = data.get("pools_gym")
        sa = data.get("finnish_sauna")

        w.writerow([
            ts_utc,
            pg[0] if pg else "",
            pg[1] if pg else "",
            sa[0] if sa else "",
            sa[1] if sa else "",
        ])

def main():
    if not within_opening_hours():
        print("Outside 06:00–22:00 Europe/Prague. Skipping.")
        return

    ts_utc = datetime.now(timezone.utc).isoformat()
    data = fetch_counts()
    append_csv("data/occupancy.csv", ts_utc, data)
    print(ts_utc, data)

if __name__ == "__main__":
    main()
