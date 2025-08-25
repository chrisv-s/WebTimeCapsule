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

## Project Abstract (for the presentation I did)

Visualize how a website changes over time using Wayback Machine snapshots.  
Media-art angle: compare archived screenshots pixel-by-pixel, with optional glitch or B/W effects.  
Modular pipeline + a Pygame interface to explore a timeline of versions.  
Focus on visual diffs, not HTML/JS parsing.

### Sources & Access

- **Wayback Machine (WBM)** + **Waybackpack (WBP)** — get snapshot URLs.  
  Repo: https://github.com/jsvine/waybackpack

### Screenshotting

- **Playwright** (headless browser) — open each snapshot and save a screenshot.  
  Repo: https://github.com/microsoft/playwright  
- Keep consistent resolution; store images to a folder.

### Analysis (Image Diff)

- **Pillow** (`PIL`) — image operations.  
  Repo: https://github.com/python-pillow/Pillow  
- `ImageChops.difference(A, B)` → highlights pixel changes between two screenshots.  
- Use the diff as a mask; optionally stylize (glitch / B&W).

### Pygame UI Prototype:
Built a basic Pygame window prototype to display images and navigate between them using arrow keys, laying groundwork 
for an interactive timeline interface.

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

# Documentation - 12.08.2025

## Step 2 – Taking Screenshots with Playwright

Now that I have my list of URLs, the next step is to visit each one and save an image of the homepage.  
This step turned out to be more tricky than I thought.

---

### Research & Approach

I decided to use **Playwright**, a browser automation library, because:

- It can run **headless** (no visible browser window), which makes it run faster.
- I can set the **viewport size** so all screenshots are consistent.
- I can run **JavaScript inside the page** to clean up elements I don’t want in the image (like the Wayback Machine toolbar).

I prompted ChatGPT to write me a small JavaScript snippet in `_remove_wayback_banner()` to delete any elements with IDs starting with `wm-` (plus a few known extras).  
This made my screenshots cleaner and easier to compare later.

---

### Difficulties

- **Slow-loading snapshots**:  
  Some snapshots load very slowly or never finish loading, which froze my code.  
  → I solved this by setting timeouts (60 seconds max per page).

- **Images not fully loaded**:  
  Sometimes a screenshot would capture half-rendered content.  
  → I added a `wait_for_function` check that waits until all images report as “loaded” before saving the screenshot.

- **Occasional blank or broken pages**:  
  → I added retries so if the first attempt fails, it tries again before skipping.

---

### Reflection

At first, I thought this step would be “the easy part”, but it actually required more problem-solving than expected.  
Working with archived pages is unpredictable: some load perfectly, others hang forever, and a few crash the browser.  
By adding **timeouts, retries, and cleanup code snippets**, I made the process much more reliable. I will probably have 
to come back later to this part and tweak a few things.

## Documentation – 23.08.2025  

### Step 3 – Viewing & Playing with the Results  

Once I had my screenshots and the pixel-difference masks, I wanted a way to actually **look at them** and explore the changes — not just stare at static files.  

That’s where **Pygame** comes in.  

I built a small interface that works like a timeline. You drag a slider to move through time, and the screenshots fade into each other instead of cutting abruptly:  

- At the start of a segment, the first image is fully visible.  
- As you drag toward the middle, it fades out to 50% while the next one fades in at 50%.  
- Past the middle, the second image takes over until it’s fully visible.  

This smooth fading isn’t just for looks — it’s tied to my **glitch effect** (generated earlier in `process_images.py`). The glitch only shows up when you’re between two images, and it’s strongest right at the 50/50 midpoint.  
 
- Screenshots always keep their **original aspect ratio** (no stretching). If they don’t fit, I just add black bars  
- The glitch layer is scaled and positioned exactly like the screenshots, so it always lines up.  
- The UI itself has a border frame, a slider at the bottom, and a small date label in the bottom-right corner (pulled from the screenshot’s filename).  

Instead of calculating differences on the fly (which would lag), I pre-generate and save all glitch images with `process_images.py`. Then the Pygame viewer just loads and shows them.

## Documentation – 24.08.2025  

Originally the viewer always showed the glitch overlay, even when the slider was snapped to a single screenshot.  
That made the interface confusing.  

I changed it so that:

- **Cross-fading**:  
  - The slider smoothly blends between screenshot A and B.  
  - The glitch overlay is only visible while sliding between them.

- **Rotated date labels**:  
  - Instead of small text in the bottom-right corner, dates are now rotated vertically and placed on the right-hand side of the frame.  
  - This makes it cleaner and avoids overlapping with the image content.  

- **Slider tick marks**:  
  - Each screenshot is marked with a small line on the slider bar.  
  - This gives a clear visual cue of how many snapshots there are and where they fall on the timeline.  

### Updates to `main.py`

The old version asked the user to enter a snapshot frequency in days, then filtered manually.  
This was clunky and often still returned too many snapshots, making the workflow very slow (especially becuase the screenshots take a lot of time)

I simplified it to:

- **Even sampling**:  
  - No matter how many snapshots are returned from the Wayback Machine, only up to **5 snapshots** are kept.  
  - These 5 are **spread evenly** across the chosen date range 

- **Simplified date input**:  
  - Dates are parsed using `dateutil.parser`, which accepts many common formats (e.g. `2020-01-01`, `Jan 2020`, `1/5/21`).  
  - Users can also just press **Enter** for the earliest possible date or today’s date.  

- **Showing the workflow**:  
  - Steps are clearly printed (`[STEP 1] … [STEP 4]`).  
  - After snapshot selection, the process automatically moves through screenshotting, analysis, and finally launches the Pygame viewer.  

These changes keep the tool fast (no more waiting for 20+ screenshots) and much more user-friendly in my opinion. Of course 
it is dissapointing that the total number of screenshots analysed is so small... maybe I will find another solution for that.

### Final Documentation (25.08.25)

