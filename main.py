# main.py
from pathlib import Path
import numpy as np
from datetime import datetime, date
from dateutil import parser
from get_url import get_snapshots
from screenshot import take_screenshots
from process_images import analyse_all
from viewer import run_viewer

SNAPSHOT_FILE = Path("data/snapshot_urls.txt")
SCREENSHOT_DIR = Path("media/screenshots")
SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
MAX_SNAPS = 5

def clean_domain(domain: str) -> str:
    return domain.removeprefix("http://").removeprefix("https://").strip("/")

def parse_timestamp(url: str) -> datetime:
    ts = url.split("/web/")[1].split("/")[0]
    return datetime.strptime(ts, "%Y%m%d%H%M%S")

def filter_by_frequency(urls, freq_days: int):
    """Stub for now – not used, just here for compatibility."""
    pass

def pick_evenly(urls, max_snaps=5):
    if len(urls) <= max_snaps:
        return urls
    idxs = np.linspace(0, len(urls)-1, max_snaps, dtype=int)
    return [urls[i] for i in idxs]

def step(n, msg):
    print(f"\n[STEP {n}] {msg}...")

def main():
    print(f"\n === Website Time Capsule ===\n")

    # --- Step 0: Ask for basic info ---
    domain = clean_domain(input("Enter website domain (e.g. www.example.com): ").strip())

    raw_start = input("Start date (press Enter for earliest): ").strip()
    raw_end   = input("End date   (press Enter for today): ").strip()

    if raw_start:
        start_date = parser.parse(raw_start).strftime("%Y%m%d")
    else:
        start_date = "19960101"   # Wayback earliest

    if raw_end:
        end_date = parser.parse(raw_end).strftime("%Y%m%d")
    else:
        end_date = date.today().strftime("%Y%m%d")

    # --- Step 1: Get snapshots ---
    step(1, "Checking available snapshots")
    all_urls = get_snapshots(domain=domain, start_date=start_date, end_date=end_date, frequency_days=1)
    print(f"Total snapshots found: {len(all_urls)}")
    if not all_urls:
        print("ERROR: No snapshots found.")
        return

    # Limit snapshots to maximum of 5
    filtered = pick_evenly(all_urls, MAX_SNAPS)
    print(f"Using {len(filtered)} snapshot(s).")

    SNAPSHOT_FILE.write_text("\n".join(filtered), encoding="utf-8")

    # --- Step 2: Take screenshots ---
    step(2, "Taking screenshots")
    saved, skipped = take_screenshots(
        input_file=str(SNAPSHOT_FILE),
        out_dir=str(SCREENSHOT_DIR),
        viewport=(1280, 800),
        retries=2,
        wait_seconds_after_load=2
    )
    print(f"Screenshots saved: {len(saved)}, skipped: {len(skipped)}")

    # --- Step 3: Analyse & create glitches ---
    step(3, "Analysing screenshots & generating glitches")
    analyse_all()

    # --- Step 4: Launch viewer ---
    step(4, "Launching viewer")
    run_viewer()

if __name__ == "__main__":
    main()

