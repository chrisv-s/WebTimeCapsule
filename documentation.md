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
