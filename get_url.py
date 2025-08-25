import requests # I need this to make requests to the Waybackmachine API

from datetime import datetime
from pathlib import Path

# I need this function so I can cover both HTTP and HTTPS snapshots, not to miss any
# archived versions, and keeping my code modular
# source: https://aws.amazon.com/compare/the-difference-between-https-and-http/

def fetch_snapshots_for_protocol(proto_url, start_date, end_date):
    cdx_url = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": proto_url,
        "from": start_date.replace("-", ""),
        "to": end_date.replace("-", ""),
        "output": "json",
        "fl": "timestamp",
        "filter": "statuscode:200",
        "collapse": "digest"
    }

    try:
        resp = requests.get(cdx_url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

    # ChatGPT prompt: "Give me Python code that calls an API with requests, prints an error if it fails or if the JSON is invalid,
    # "and returns an empty list in both cases."

    except requests.RequestException as e:
        print(f"ERROR: Failed to get snapshots for {proto_url}: {e}")
        return []
    except ValueError:
        print(f"ERROR: Non-JSON response from CDX API for {proto_url}")
        return []

    return sorted([row[0] for row in data[1:]])

def get_snapshots(domain, start_date, end_date, frequency_days=90, save_to=None):
    protocol_map = {}
    for proto in ["http://", "https://"]:
        ts_list = fetch_snapshots_for_protocol(proto + domain, start_date, end_date)
        for ts in ts_list:
            protocol_map[ts] = proto  # remember which protocol this timestamp came from

    # Sort timestamps and filter by frequency
    archive_urls = []
    last_date = None
    for ts in sorted(protocol_map.keys()):
        snapshot_dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
        if not last_date or (snapshot_dt - last_date).days >= frequency_days:
            proto = protocol_map[ts]
            archive_urls.append(f"https://web.archive.org/web/{ts}/{proto}{domain}")
            last_date = snapshot_dt

    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        with open(save_to, "w", encoding="utf-8") as f:
            for url in archive_urls:
                f.write(url + "\n")
        print(f"INFO: Saved {len(archive_urls)} snapshot URLs to {save_to}")

    return archive_urls

