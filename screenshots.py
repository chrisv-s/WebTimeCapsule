from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time

# ChatGPT prompt: "Write a Python function that removes the Wayback Machine’s toolbar and banners from a webpage when
# using Playwright. It should run JavaScript in page.evaluate() to select and delete all elements with IDs starting with wm-

def _remove_wayback_banner(page):
    page.evaluate("""
    () => {
      document.querySelectorAll('[id^="wm-"], #donato, #banner').forEach(el => el.remove());
      document.body.style.marginTop = '0';
    }
    """)

def take_screenshots(input_file="data/snapshot_urls.txt", out_dir="media/screenshots", viewport=(1280, 800), retries=1, wait_seconds_after_load=1):
    input_path = Path(input_file)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return [], [] # I return saved and skipped as an empty tuple so the code doesn't break

    urls = [u.strip() for u in input_path.read_text(encoding="utf-8").splitlines() if u.strip()]
    if not urls:
        print("ERROR: URL list is empty.")
        return [], []

    saved, skipped = [], []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})

        # I increase the loading time for slow pages
        page.set_default_navigation_timeout(60_000)
        page.set_default_timeout(60_000)

        # I name the screenshots after their timestamp
        for url in urls:
            ts = url.split("/web/")[1].split("/")[0]
            file_path = out_path / f"{ts}.png"

        # Retry loop in case something went wrong the first time
            for attempt in range(retries + 1):
                try:
                    print(f"INFO: Screenshotting {url}")
                    page.goto(url, wait_until="load")

                    _remove_wayback_banner(page)

                    # This part makes the script wait until all images report as fully loaded (img.complete)
                    # and actually have pixels (naturalWidth > 0).
                    try:
                        page.wait_for_function(
                            "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)"
                        )
                    except Exception:
                        pass

                    if wait_seconds_after_load > 0:
                        time.sleep(wait_seconds_after_load)

                    # Save screenshot (I don't want the full page, just the viewport I set)
                    page.screenshot(path=str(file_path), full_page=False)
                    saved.append(str(file_path))
                    break

                except PlaywrightTimeout:
                    print(f"ERROR: Timeout at {url}")
                    if attempt == retries:
                        skipped.append(url)
                except Exception as idk:
                    print(f"[WARN] Error with {url}: {idk}")
                    if attempt == retries:
                        skipped.append(url)

        browser.close()

    print(f"Saved {len(saved)} screenshot(s) to {out_path}")
    if skipped:
        print(f"Skipped {len(skipped)} URL(s) due to errors/timeouts.")
    else:
        print("No skips — all snapshots captured.")

    return saved, skipped

