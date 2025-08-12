# src/visualizer.py
import re, pygame
from math import floor
from pathlib import Path
from datetime import datetime
from process_images import list_screenshots, analyse_pair

# UI constants – I chose these values so the interface feels spacious but not too big
UI_H, FPS, FRAME, MARGIN = 110, 60, 24, 60
BAR_H, HANDLE_W, HANDLE_H = 10, 18, 28

def parse_date(name):
    """I use the filename to extract the timestamp and format it nicely as YYYY-MM-DD."""
    d = re.sub(r"\D", "", Path(name).stem)
    for f in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
        try:
            return datetime.strptime(d, f).strftime("%Y-%m-%d")
        except:
            pass
    return Path(name).stem

def clamp(x, a, b):
    """Quick helper so I don’t go out of range."""
    return max(a, min(b, x))

def load_scaled_centered(path, max_size):
    """
    I load each screenshot, scale it proportionally so it fits in my image area
    and return both the scaled image and the offset needed to center it (letterbox/pillarbox).
    """
    img = pygame.image.load(str(path)).convert()
    iw, ih = img.get_size()
    max_w, max_h = max_size
    scale = min(max_w / iw, max_h / ih)
    new_size = (int(iw * scale), int(ih * scale))
    img = pygame.transform.smoothscale(img, new_size)
    pos = ((max_w - new_size[0]) // 2, (max_h - new_size[1]) // 2)
    return img, pos

def main():
    pygame.init()
    sw, sh = pygame.display.Info().current_w, pygame.display.Info().current_h
    screen = pygame.display.set_mode((sw, sh))
    clock = pygame.time.Clock()
    font, big = pygame.font.SysFont(None, 22), pygame.font.SysFont(None, 28)

    # My image display area is the screen minus the frame and the bottom UI bar
    iw, ih = sw - 2 * FRAME, sh - 2 * FRAME
    img_wh = (iw, ih - UI_H)

    # Load screenshot filenames from analyse.py helper
    shots = list_screenshots()
    if not shots:
        print("[ERROR] No screenshots found in media/screenshots.")
        return

    # I use dictionaries to store already scaled images and pre-computed glitch layers
    scaled, glitch = {}, {}

    def gi(i):
        """Get image i, scaled + centered, from cache or load if not there."""
        if i not in scaled:
            img, pos = load_scaled_centered(Path("media/screenshots") / shots[i], img_wh)
            scaled[i] = (img, pos)
        return scaled[i]

    pos, drag, run = 0.0, False, True

    while run:
        # Event loop – handles quitting, slider dragging, and snapping
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                run = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                by = FRAME + img_wh[1] + 38
                if pygame.Rect(FRAME + MARGIN, by - 15, iw - 2 * MARGIN, BAR_H + 30).collidepoint((mx, my)):
                    drag = True
            elif e.type == pygame.MOUSEBUTTONUP:
                drag = False
                pos = float(int(round(pos)))  # snap to nearest image when letting go

        # Update slider position if dragging
        if drag and len(shots) > 1:
            mx = pygame.mouse.get_pos()[0]
            bx = FRAME + MARGIN
            bw = iw - 2 * MARGIN
            pos = clamp((mx - bx) / bw, 0, 1) * (len(shots) - 1)

        # Figure out which two images I’m between
        i = int(floor(pos))
        j = clamp(i + 1, 0, len(shots) - 1)
        u = 0 if i == j else (pos - i)  # 0..1 between the two
        g = 2 * min(u, 1 - u)  # glitch alpha: peaks at 0.5

        # Draw background and inner frame
        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (18, 18, 18), (FRAME, FRAME, iw, ih), border_radius=12)

        # Fade between A and B
        (A, posA), (B, posB) = gi(i), gi(j)
        if u == 0:
            screen.blit(A, (FRAME + posA[0], FRAME + posA[1]))
        elif u == 1:
            screen.blit(B, (FRAME + posB[0], FRAME + posB[1]))
        else:
            a = A.copy(); a.set_alpha(int(255 * (1 - u)))
            b = B.copy(); b.set_alpha(int(255 * u))
            screen.blit(a, (FRAME + posA[0], FRAME + posA[1]))
            screen.blit(b, (FRAME + posB[0], FRAME + posB[1]))

        # Glitch overlay – scaled + positioned same as images
        key = (i, j)
        if key not in glitch:
            gs, _ = analyse_pair(i, j)
            gs_scaled = pygame.transform.smoothscale(gs, A.get_size()).convert()
            glitch[key] = (gs_scaled, posA)
        gl_surf, gl_pos = glitch[key]
        gl = gl_surf.copy()
        gl.set_alpha(int(255 * g))
        screen.blit(gl, (FRAME + gl_pos[0], FRAME + gl_pos[1]))

        # Date label (I keep it simple: just the left image’s date)
        label = big.render(parse_date(shots[i]), True, (240, 240, 240))
        screen.blit(label, (FRAME + iw - label.get_width() - 12,
                            FRAME + img_wh[1] - label.get_height() - 10))

        # Slider drawing
        by = FRAME + img_wh[1] + 38
        bx = FRAME + MARGIN
        bw = iw - 2 * MARGIN
        pygame.draw.rect(screen, (80, 80, 80), (bx, by, bw, BAR_H), border_radius=6)
        hx = bx if len(shots) == 1 else bx + int(bw * (pos / (len(shots) - 1)))
        h = pygame.Rect(0, 0, HANDLE_W, HANDLE_H)
        h.center = (hx, by + BAR_H // 2)
        pygame.draw.rect(screen, (200, 60, 60), h, border_radius=6)
        pygame.draw.rect(screen, (240, 180, 180), h, 2, border_radius=6)
        screen.blit(font.render("Drag slider • ESC to quit", True, (210, 210, 210)), (bx, by + 32))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
