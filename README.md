# WebTimeCapsule

---

This media art project visualizes how a website changes over time using snapshots from the Wayback Machine. 
By taking automated screenshots of archived pages and comparing them pixel-by-pixel, the project highlights visual 
differences through glitch-inspired effects.

## Installation

- Waybackpack — Get URLs from Wayback Machine
- Playwright — Take screenshots of web pages
- Pillow — Load and compare images pixel-by-pixel
- NumPy — Pixel data processing and math
- Pygame — Interactive UI

Install required dependencies:

```bash

pip install -r requirements.txt
```

## Usage

### 1. Install requirements

```
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the program

Start the workflow from the terminal:
`python main.py`

### 3. Enter inputs

You’ll be asked for:

- Website domain (e.g. www.example.com)
- Start date (type YYYY-MM-DD, or just press Enter for the earliest snapshot)
- End date (type YYYY-MM-DD, or press Enter for today’s date)

The program will then fetch available Wayback Machine snapshots and automatically pick up to 5 evenly spread snapshots between the two dates.

### 4. Wait for screenshots

Playwright will open archived pages and save consistent screenshots to media/screenshots/.

Any differences between pairs of screenshots are pre-processed into:

- Masks (media/masks/) → black/white images showing changed areas. 
- Glitches (media/glitches/) → colorful overlays highlighting changes.

### 5. Explore in the viewer

A Pygame window will launch automatically:

- Drag the slider at the bottom to scrub through time.
- Screenshots cross-fade smoothly from one to the next.
- The glitch overlay appears only in-between snapshots, strongest at the midpoint.
- Vertical date labels appear on the right-hand side.
- Tick marks on the slider show where each snapshot is.
- Press ESC to quit the viewer.