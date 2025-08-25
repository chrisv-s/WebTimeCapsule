# Importing all the dependecies
from pathlib import Path
import numpy as np
from datetime import datetime, date
from dateutil import parser
from get_url import get_snapshots
from screenshot import take_screenshots
from process_images import analyse_all
from viewer import run_viewer

SNAPSHOT_FILE = Path("data/snapshot_urls.txt")   # where snapshot URLs will be stored
SCREENSHOT_DIR = Path("media/screenshots")       # where screenshots will be saved
SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
MAX_SNAPS = 5   # limit on how many snapshots to process (avoids long waits from screenshots.py)

def clean_domain(domain: str) -> str:
    """
    Removes 'http://' or 'https://' and trailing slashes from a domain string.
    This that the domain is in a clean format for the queries. Example: 'https://www.example.com/' -> 'www.example.com'
    """
    return domain.removeprefix("http://").removeprefix("https://").strip("/")

def parse_timestamp(url: str) -> datetime:
    """
    This extracts the timestamp (YYYYMMDDHHMMSS) from a Wayback Machine snapshot URL
    and return it as a datetime object.
    """
    ts = url.split("/web/")[1].split("/")[0]
    return datetime.strptime(ts, "%Y%m%d%H%M%S")

def filter_by_frequency(urls, freq_days: int):
    pass

def pick_evenly(urls, max_snaps=5):
    if len(urls) <= max_snaps:
        return urls
    idxs = np.linspace(0, len(urls)-1, max_snaps, dtype=int)  # picks snapshots evenly based on the given time frame
    return [urls[i] for i in idxs]

# print function because this is often used
def step(n, msg):
    print(f"\n[STEP {n}] {msg}...")

def main():
    print(f"\n === Website Time Capsule ===\n")

    domain = clean_domain(input("Enter website domain (e.g. www.example.com): ").strip())

    raw_start = input("Start date (press Enter for earliest): ").strip()
    raw_end   = input("End date   (press Enter for today): ").strip()

    # Uses dateutil.parser so the user can type dates flexibly (YYYY-MM-DD, 2010, etc.)
    if raw_start:
        start_date = parser.parse(raw_start).strftime("%Y%m%d")
    else:
        start_date = "19960101"   # Wayback earliest available

    if raw_end:
        end_date = parser.parse(raw_end).strftime("%Y%m%d")
    else:
        end_date = date.today().strftime("%Y%m%d")

    # 1. Get URLs
    step(1, "Checking available snapshots")
    all_urls = get_snapshots(domain=domain, start_date=start_date, end_date=end_date, frequency_days=1)
    print(f"Total snapshots found: {len(all_urls)}")
    if not all_urls:
        print("ERROR: No snapshots found.")
        return

    filtered = pick_evenly(all_urls, MAX_SNAPS)
    print(f"Using {len(filtered)} snapshot(s).")

    SNAPSHOT_FILE.write_text("\n".join(filtered), encoding="utf-8")

    # 2. Takes scrennshots
    step(2, "Taking screenshots")
    saved, skipped = take_screenshots(input_file=str(SNAPSHOT_FILE), out_dir=str(SCREENSHOT_DIR),
        viewport=(1280, 800),     # I fixed browser size for consistency
        retries=2,                # retry failed snapshots twice
        wait_seconds_after_load=2 # wait a bit for images to load before screenshot
    )
    print(f"Screenshots saved: {len(saved)}, skipped: {len(skipped)}")

    # 3. Analyses screenshots & create glitch overlays
    step(3, "Analysing screenshots & generating glitches")
    analyse_all()

    # Launches viewer
    step(4, "Launching viewer")
    run_viewer()

if __name__ == "__main__":
    main()
