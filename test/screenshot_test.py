# draft/messing around
from playwright.sync_api import sync_playwright

# The snapshot URL from the Wayback Machine
snapshot_url = "https://web.archive.org/web/20100115094530/http://example.com"

# Where to save the screenshot
output_file = "screenshot_test.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # headless=True = no GUI
    page = browser.new_page()

    # Go to the snapshot URL
    page.goto(snapshot_url, timeout=60000)  # 60 sec timeout

    # Optional: wait for the page to fully load
    page.wait_for_load_state("networkidle")

    # Take screenshot
    page.screenshot(path=output_file, full_page=True)

    print(f"Screenshot saved to {output_file}")
    browser.close()