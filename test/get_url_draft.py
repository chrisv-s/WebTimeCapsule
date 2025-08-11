import requests
from datetime import datetime
from pathlib import Path

# NOTE:
# Currently only fetches snapshots using HTTPS.
# In the future, I might extend this to check both HTTP and HTTPS

def fetch_snapshots(proto_url, start_date, end_date):
    """Fetch snapshot timestamps for a given URL (currently HTTPS only)."""
    cdx_url = "http://web.archive.org/cdx/search/cdx"
    params = {
        "url": proto_url,
        "from": start_date.replace("-", ""),
        "to": end_date.replace("-", ""),
        "output": "json",
        "fl": "timestamp",
        "filter": "statuscode:200",
        "collapse": "digest"
    }


# ChatGPT prompt: "Can you give me a Python code snippet that gets data from a URL using requests, with a timeout,
# and shows a clear error message if something goes wrong?"

    try:
        resp = requests.get(cdx_url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch snapshots for {proto_url}: {e}")
        return []
    except ValueError:
        print(f"[ERROR] Non-JSON response from CDX API for {proto_url}")
        return []

    # First row is the header: ["timestamp"]
    return sorted([row[0] for row in data[1:]])


def get_snapshots(domain, start_date, end_date, frequency_days=90, save_to=None):
    ts_list = fetch_snapshots("https://" + domain, start_date, end_date)

    archive_urls = []
    last_date = None
    for ts in ts_list:
        snapshot_dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
        if not last_date or (snapshot_dt - last_date).days >= frequency_days:
            archive_urls.append(f"https://web.archive.org/web/{ts}/https://{domain}")
            last_date = snapshot_dt

    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        with open(save_to, "w", encoding="utf-8") as f:
            for url in archive_urls:
                f.write(url + "\n")
        print(f"[INFO] Saved {len(archive_urls)} snapshot URLs to {save_to}")

    return archive_urls


if __name__ == "__main__":
    domain = input("Enter website domain (without http/https): ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    freq_days = int(input("Frequency in days: "))

    get_snapshots(domain, start_date, end_date, freq_days, save_to="data/snapshot_urls.txt")
