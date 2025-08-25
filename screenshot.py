from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

INPUT_FILE_DEFAULT = "data/snapshot_urls.txt"
OUT_DIR_DEFAULT = "media/screenshots"

# ChatGPT prompt: "Write a Python function that removes the Wayback Machine’s toolbar and banners from a webpage when
# using Playwright. It should run JavaScript in page.evaluate() to select and delete all elements with IDs starting with wm-"
WAYBACK_CLEAN_JS = """
() => {
  const selAll = (q) => document.querySelectorAll(q);
  [...selAll('[id^="wm-"]'), ...selAll('#donato'), ...selAll('#banner')]
    .forEach(el => el && el.remove());
  if (document.body) document.body.style.marginTop = '0';
}
"""

def _remove_wayback_banner(page):
    page.evaluate(WAYBACK_CLEAN_JS)

def _load_page(page, url):
    """
    - Opens the URL with a generous timeout.
    - Waits until the <body> is present (so we know the page really exists).
    - Removes the Wayback Machine toolbar/banner.

    Use this first — it gives the cleanest and most complete screenshot.
    """
    page.goto(url, wait_until="load", timeout=20_000)
    page.wait_for_selector("body", timeout=5_000)
    _remove_wayback_banner(page)


def _best_effort_path(page, url):
    """
    The fallback screenshot method (if _slow_path fails).
    - Tries to open the page quickly, even if not all assets load.
    - Waits only briefly for a <body> tag.
    - Still removes Wayback banners/toolbars.
    - May result in partial content, but better than nothing I guess
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=8_000)
    except PlaywrightTimeout:
        pass
    try:
        page.wait_for_selector("body", timeout=2_000)
    except PlaywrightTimeout:
        pass

    _remove_wayback_banner(page)

def take_screenshots(input_file=INPUT_FILE_DEFAULT, out_dir=OUT_DIR_DEFAULT, viewport=(1280, 800), headless=True):
    input_path = Path(input_file)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # I return saved and skipped as an empty tuple so the code doesn't break
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return [], []

    urls = [u.strip() for u in input_path.read_text(encoding="utf-8").splitlines() if u.strip()]
    if not urls:
        print("[ERROR] URL list is empty.")
        return [], []

    saved, skipped = [], []

    with sync_playwright() as p:
        # Launch a Chromium browser (headless=True means no visible window).
        browser = p.chromium.launch(headless=headless)

        #  I used AI to write this particular part:
        # Creates a new browser context (like a fresh browser profile).
        # - Sets the viewport size for consistent screenshots.
        # - Ignores HTTPS errors (important because many archived pages have broken certificates).
        context = browser.new_context(
            viewport={"width": viewport[0], "height": viewport[1]},
            ignore_https_errors=True,
        )

        # "I used AI to write this particular part:
        # Inject a small JavaScript snippet into every page BEFORE it loads.
        # This removes Wayback Machine’s toolbar/banner and also disables CSS animations
        context.add_init_script("""
          document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('[id^="wm-"], #donato, #banner')
              .forEach(el => el.remove());
            if (document.body) document.body.style.marginTop = '0';
            const style = document.createElement('style');
            style.type = 'text/css';
            style.textContent = "*, *::before, *::after { animation: none !important; transition: none !important; }";
            document.head.appendChild(style);
          });
        """)

        # This loopS through each Wayback Machine snapshot URL
        for url in urls:
            try:
                # Extract the timestamp (the long YYYYMMDDhhmmss number in the URL)
                ts = url.split("/web/")[1].split("/")[0]
            except Exception:
                ts = "snapshot"  # fallback if timestamp parsing fails

            # I define where to save the screenshot
            file_path = out_path / f"{ts}.png"
            print(f"[INFO] Processing snapshot {ts} ...")

            # Opens a new browser tab for this snapshot
            page = context.new_page()
            success = False

            try:
                # First tries the "slow path" (full load, clean page, best quality)
                _slow_path(page, url)
                page.screenshot(path=str(file_path), full_page=False)
                success = True
            except Exception:
                # If that fails (e.g., page hangs), falls back to "best effort"
                print("  ...waiting, retrying...")
                try:
                    _best_effort_path(page, url)
                    page.screenshot(path=str(file_path), full_page=False)
                    success = True
                except Exception:
                    # If even best effort fails, skip this snapshot
                    print("  ...skipped, could not capture this snapshot.")

            try:
                page.close()
            except Exception:
                pass

            if success:
                saved.append(str(file_path))
            else:
                skipped.append(url)

        # Close the browser context and Chromium instance
        context.close()
        browser.close()

    # Summary output
    print(f"\n[INFO] Saved {len(saved)} screenshot(s) to {out_path}")
    if skipped:
        print(f"[INFO] Skipped {len(skipped)} snapshot(s).")
    else:
        print("[INFO] All snapshots captured successfully.")
    return saved, skipped

if __name__ == "__main__":
    saved, skipped = take_screenshots()
    print("\n=== DONE ===")
    print(f"Saved: {len(saved)}")
    print(f"Skipped: {len(skipped)}")
