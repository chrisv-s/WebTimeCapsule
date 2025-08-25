import pygame
from pathlib import Path
from math import floor
from datetime import datetime
from process_images import list_screenshots

UI_H = 110         # reserved height at bottom for slider + UI
FPS = 60           # frames per second for smooth animations
FRAME = 60         # margin around the content area
BAR_H = 10         # slider bar height
HANDLE_W = 18      # slider handle width
HANDLE_H = 28      # slider handle height

GLITCH_DIR = Path("media/glitches")
MASK_DIR = Path("media/masks")

def parse_date_from_filename(name: str) -> str:
    """
    I had AI write me this part of the code:
    Extracts a date string (YYYY-MM-DD) from a filename so I can show the date on the right side.
    Filenames usually look like 20100115094530.png. If parsing fails, it just return the filename itself.
    """
    stem = Path(name).stem
    digits = "".join(ch for ch in stem if ch.isdigit())
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
        try:
            return datetime.strptime(digits, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return stem

def clamp(x, a, b):
    """Clamp a number x so it always stays between a and b. This is a helper for example when sliding so the value is kept betweeen 0.0–1.0"""
    return max(a, min(b, x))

def load_scaled_centered(path: Path, max_size: tuple[int, int]):
    """
    This loads an image and resizes it so it fits inside max_size without distortion.
    Returns the scaled Pygame surface and an (x,y) offset so it is centered.
    """
    surf = pygame.image.load(str(path)).convert()
    iw, ih = surf.get_size()
    mw, mh = max_size
    scale = min(mw / iw, mh / ih)
    new_size = (int(iw * scale), int(ih * scale))
    surf = pygame.transform.smoothscale(surf, new_size)
    pos = ((mw - new_size[0]) // 2, (mh - new_size[1]) // 2)
    return surf, pos

# This is the main code:
def run_viewer():
    pygame.init()
    sw, sh = 1200, 800   # window size
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Snapshot Viewer")
    clock = pygame.time.Clock()
    font_small = pygame.font.SysFont(None, 18)
    font_big = pygame.font.SysFont(None, 28)

    # I need to define the inner area for the content (images)
    inner_w, inner_h = sw - 2 * FRAME, sh - 2 * FRAME
    image_area = (inner_w, inner_h - UI_H)

    screenshots = list_screenshots()
    if not screenshots:
        print("[INFO] No screenshots found.")
        return

    # I store the images in caches to avoid reloading/re-scaling the same images
    scaled_cache = {}    # idx -> (surface, (x,y))
    overlay_cache = {}   # (s1, s2, kind) -> overlay surface

    def get_image(idx: int):
        if idx not in scaled_cache:
            scaled_cache[idx] = load_scaled_centered(screenshots[idx], image_area)
        return scaled_cache[idx]

    def get_overlay(idx: int):
        """
        This loads the glitch or mask overlay for the pair (idx, idx+1).
        """
        if idx >= len(screenshots) - 1:
            return None

        name_i = screenshots[idx].stem
        name_j = screenshots[idx + 1].stem

        # glitch overlay
        key_g = (name_i, name_j, "glitch")
        if key_g not in overlay_cache:
            gpath = GLITCH_DIR / f"{name_i}__{name_j}.png"
            if gpath.exists():
                base_surf, pos = get_image(idx)
                ov = pygame.image.load(str(gpath)).convert()
                ov = pygame.transform.smoothscale(ov, base_surf.get_size())
                overlay_cache[key_g] = (ov, pos)
        if key_g in overlay_cache:
            ov, pos = overlay_cache[key_g]
            return ov, pos, "glitch"

        return None

    slider_pos = 0.0
    dragging = False  # looks whether user is dragging the slider
    running = True

    while running:
        # This handles events (quit, keys, mouse)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                dragging = True
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                dragging = False
                # snaps slider to nearest screenshot index
                slider_pos = float(int(round(slider_pos)))

        # updates slider position if dragging
        if dragging and len(screenshots) > 1:
            mx = pygame.mouse.get_pos()[0]
            t = clamp((mx - FRAME) / max(1, inner_w), 0.0, 1.0)
            slider_pos = t * (len(screenshots) - 1)

        i = int(floor(slider_pos))
        j = clamp(i + 1, 0, len(screenshots) - 1)
        u = 0.0 if i == j else (slider_pos - i)

        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (18, 18, 18), (FRAME, FRAME, inner_w, inner_h), border_radius=12)

        # This draws the images with cross-fade
        (surf_a, pos_a) = get_image(i)
        (surf_b, pos_b) = get_image(j)
        if u == 0:  # shows only A
            screen.blit(surf_a, (FRAME + pos_a[0], FRAME + pos_a[1]))
        elif u == 1:  # shows only B
            screen.blit(surf_b, (FRAME + pos_b[0], FRAME + pos_b[1]))
        else:  # blends A and B
            a = surf_a.copy();
            a.set_alpha(int(255 * (1 - u)))
            b = surf_b.copy();
            b.set_alpha(int(255 * u))
            screen.blit(a, (FRAME + pos_a[0], FRAME + pos_a[1]))
            screen.blit(b, (FRAME + pos_b[0], FRAME + pos_b[1]))

        # This draws the glitch overlay (only between A and B)
        if 0 < u < 1:
            ov_info = get_overlay(i)
            if ov_info:
                ov, pos_ov, kind = ov_info
                ov_draw = ov.copy()
                glitch_strength = 2 * min(u, 1 - u)  # strongest in the middle
                ov_draw.set_alpha(int(255 * glitch_strength))
                screen.blit(ov_draw, (FRAME + pos_ov[0], FRAME + pos_ov[1]))

        # I had AI help me write this part of the code:
        # This puts rotated date label on right side
        if u == 0:
            label = parse_date_from_filename(screenshots[i].name)
        elif u == 1:
            label = parse_date_from_filename(screenshots[j].name)
        else:
            label = f"{parse_date_from_filename(screenshots[i].name)} to {parse_date_from_filename(screenshots[j].name)}"
        label_surf = font_small.render(label, True, (240, 240, 240))
        label_surf = pygame.transform.rotate(label_surf, 90)
        screen.blit(label_surf, (
            FRAME + inner_w - label_surf.get_width() - 5,
            FRAME + 20
        ))

        # This adds the slider bar with tick marks
        bar_y = FRAME + (inner_h - UI_H) + 38
        pygame.draw.rect(screen, (80, 80, 80), (FRAME, bar_y, inner_w, BAR_H), border_radius=6)

        if len(screenshots) > 1:
            for k in range(len(screenshots)):
                x = FRAME + int((k / (len(screenshots) - 1)) * inner_w)
                pygame.draw.line(screen, (200, 200, 200), (x, bar_y), (x, bar_y + BAR_H), 2)

        # This draws the slider handle
        if len(screenshots) == 1:
            handle_x = FRAME
        else:
            handle_x = FRAME + int((slider_pos / (len(screenshots) - 1)) * inner_w)
        handle_rect = pygame.Rect(0, 0, HANDLE_W, HANDLE_H)
        handle_rect.center = (handle_x, bar_y + BAR_H // 2)
        pygame.draw.rect(screen, (200, 60, 60), handle_rect, border_radius=6)
        pygame.draw.rect(screen, (240, 180, 180), handle_rect, 2, border_radius=6)

        # This draws help text
        hint = font_small.render("Drag to slide between images • ESC to quit", True, (210, 210, 210))
        screen.blit(hint, (FRAME, bar_y + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()