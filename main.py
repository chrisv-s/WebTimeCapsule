from get_url import get_snapshots
from screenshots import take_screenshots

# clean user input
def clean_domain(domain):
    return domain.replace("http://", "").replace("https://", "").strip("/")

def main():
    print("=== Website Time Capsule ===\n")

    raw_domain = input("Enter website domain (e.g., www.example.com): ").strip()
    domain = clean_domain(raw_domain)

    # Maybe use a calendar interface here?
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()

    snapshot_file = "data/snapshot_urls.txt"
    screenshot_dir = "media/screenshots"

    print("\nChecking available snapshots...")

    # Is this a little inefficient?
    all_urls = get_snapshots(
        domain=domain,
        start_date=start_date,
        end_date=end_date,
        frequency_days=1
    )
    print(f"Total snapshots found: {len(all_urls)}")

    if not all_urls:
        print("ERROR: No snapshots found for given range.")
        return

    while True:
        try:
            freq_days = int(input(
                "Enter frequency in days to filter snapshots (e.g., 90): ").strip()
            )
        except ValueError:
            print("[WARN] Please enter a valid number.")
            continue

        filtered_urls = get_snapshots(
            domain=domain,
            start_date=start_date,
            end_date=end_date,
            frequency_days=freq_days
        )

        print(f"Snapshots after filtering: {len(filtered_urls)}")

        # maybe a little unnecessary...
        confirm = input("Use this filtered set? (y/n): ").strip().lower()
        if confirm == "y":
            get_snapshots(
                domain=domain,
                start_date=start_date,
                end_date=end_date,
                frequency_days=freq_days,
                save_to=snapshot_file
            )
            break

    print("\nTaking screenshots of filtered snapshots...")
    saved, skipped = take_screenshots(
        input_file=snapshot_file,
        out_dir=screenshot_dir,
        viewport=(1280, 800),
        retries=2,
        wait_seconds_after_load=2
    )

    print(f"Total snapshots processed: {len(filtered_urls)}")
    print(f"Screenshots saved: {len(saved)}")
    print(f"Screenshots skipped: {len(skipped)}")

if __name__ == "__main__":
    main()
