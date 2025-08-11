# Insert Organized Chaos :)

### What’s the plan?
- Show how a website’s homepage changed over time using snapshots from the Wayback Machine.
- Make it look cool with glitchy, pixel-by-pixel difference effects.
- Build a Pygame window so people can scroll through the timeline and see these changes.

Rough idea for project structure
```project/
│
├── media or data/
│   ├── screenshots/    
│
├── src/
│   ├── get_url.py    # get URLs from Wayback Machine
│   ├── screenshots.py # take screenshots with the help of Playwright
│   ├── process_images.py   # find differences, masks, (glitch) effects
│   ├── viewer.py           # Pygame window and controls
│   └── helper.py          # little helper functions
│
├── main.py          # runs the whole thing: download, process, view
└── requirements.txt
```

# Documentation – 11.08.2025

## Step 1 – Getting a List of URLs

Before I can do anything visual in my project — like comparing screenshots or adding any visual effects — I need to know which dates the Wayback Machine actually has versions of the website I want to analyze.

The Wayback Machine doesn’t archive a site every day or every time it changes. Instead, it takes **“snapshots”** at certain times. These are like photographs of the site on that exact date and time.

Knowing when these snapshots exist is important because:

- I can only compare two versions if I know they both exist in the archive.
- I can choose to space them out (e.g., one every 3 months) so I don’t process hundreds of almost-identical copies.

---

### Using the CDX API

For that, I can use the so-called **CDX API**, which is the Wayback Machine’s database search tool. 
You give it a website URL, and it tells you all the timestamps it has for that site.

A timestamp looks like this: 20100115094530

Which means:

- **Year:** 2010  
- **Month:** 01  
- **Day:** 15  
- **Time:** 09:45:30 UTC

Normally, **Waybackpack** uses the CDX API first, then downloads full HTML and assets for each snapshot.  
I don’t need the HTML — just the URLs for later screenshots.  
So instead of using all of Waybackpack’s code, I **reimplemented only the CDX API query** in my script and built the snapshot URLs myself, similar to how Waybackpack’s `get_archive_url()` method works.

---

### My Approach

Instead of importing the full Waybackpack downloading system, I reimplemented just the **CDX API request** part in my own Python script.

**What my code does:**

1. Ask the user for:
   - Website URL
   - Start date / End date
   - Snapshot frequency
2. Send this request to the CDX API.
3. Get back a list of timestamps.
4. Convert each timestamp into a WBM archive link, e.g.: 
https://web.archive.org/web/20100115094530/http://example.com 

5. Save these URLs.
6. Filter Wayback Machine snapshots in this step to keep the workflow efficient — removing unneeded versions **before** opening anything in the headless browser (the next step in my project).  
This way, Playwright only takes screenshots of relevant snapshots, saving time and resources.

---

The Wayback Machine is like a **giant library** with billions of “photographs” of websites, each tagged with the exact date and time it was captured. 
The **CDX API** is like the library’s **card catalog** — you can ask it which dates it has for a specific site and time period, and it returns a list of timestamps.


The base URL for the CDX API is always:

````
cdx_url = "http://web.archive.org/cdx/search/cdx"`

# Instead of always using a long URL with parameters, I store all the changing options in a Python dictionary:

params = {
    "url": url,  # site I’m checking
    "from": start_date.replace("-", ""),  # start date without dashes
    "to": end_date.replace("-", ""),  # end date without dashes
    "output": "json",  # return format
    "fl": "timestamp",  # only ask for the timestamp field
    "filter": "statuscode:200",  # only working pages
    "collapse": "digest"  # removes exact duplicates
}
````

When I run:

`resp = requests.get(cdx_url, params=params)`

…the requests library automatically builds a proper URL for me.

Source:
https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md 
