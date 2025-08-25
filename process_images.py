# src/process_image.py
from pathlib import Path
from PIL import Image
import numpy as np

# directories
SCREENSHOT_DIR = Path("media/screenshots")
GLITCH_DIR = Path("media/glitches")
MASK_DIR = Path("media/masks")
for d in (GLITCH_DIR, MASK_DIR):
    d.mkdir(parents=True, exist_ok=True)

def list_screenshots():
    """Return sorted list of screenshot paths."""
    return sorted(SCREENSHOT_DIR.glob("*.png"))

def to_rgb_array(img: Image.Image):
    """Convert PIL image to uint8 numpy array (H,W,3)."""
    return np.asarray(img.convert("RGB"), dtype=np.uint8)

def center_crop(a: Image.Image, b: Image.Image):
    """Crop both images to the same center size (min width/height)."""
    wa, ha = a.size; wb, hb = b.size
    w, h = min(wa, wb), min(ha, hb)
    def crop(img):
        W, H = img.size
        left, top = (W - w)//2, (H - h)//2
        return img.crop((left, top, left + w, top + h))
    return crop(a), crop(b)

def compute_mask(img_a, img_b, threshold=15):
    """Return (mask, alignedA, alignedB)."""
    a, b = center_crop(img_a, img_b)
    arr_a, arr_b = to_rgb_array(a).astype(int), to_rgb_array(b).astype(int)
    diff = np.abs(arr_a - arr_b).max(axis=2)
    mask = diff > threshold
    return mask, a, b

def shift(channel, dy=0, dx=0):
    """Shift 2D array by (dy,dx) without wrap-around (edges stretched)."""
    out = channel.copy(); h, w = out.shape
    if dy > 0: out[dy:,:] = out[:-dy,:]; out[:dy,:] = out[dy:dy+1,:]
    elif dy < 0: k=-dy; out[:-k,:] = out[k:,:]; out[-k:,:] = out[-k-1:-k,:]
    if dx > 0: out[:,dx:] = out[:,:-dx]; out[:,:dx] = out[:,dx:dx+1]
    elif dx < 0: k=-dx; out[:,:-k] = out[:,k:]; out[:,-k:] = out[:,-k-1:-k]
    return out

def make_glitch(img_a, img_b, mask):
    """Combine A and B with RGB shifts only where mask==True."""
    arr_a = to_rgb_array(img_a)
    arr_b = to_rgb_array(img_b)

    # channels
    r_a, g_a, b_a = arr_a[...,0], arr_a[...,1], arr_a[...,2]
    r_b, g_b, b_b = arr_b[...,0], arr_b[...,1], arr_b[...,2]

    # shifted versions
    r_a_s = shift(r_a, dx=-10)
    g_a_s = shift(g_a, dy=10)
    b_a_s = shift(b_a, dx=10)

    r_b_s = shift(r_b, dx=10)
    g_b_s = shift(g_b, dy=10)
    b_b_s = shift(b_b, dx=10)

    # start from B
    out = arr_b.copy()

    # only change where mask==True, mix A and B shifts
    out[...,0][mask] = ((r_a_s[mask] + r_b_s[mask]) // 2).astype(np.uint8)
    out[...,1][mask] = ((g_a_s[mask] + g_b_s[mask]) // 2).astype(np.uint8)
    out[...,2][mask] = ((b_a_s[mask] + b_b_s[mask]) // 2).astype(np.uint8)

    return Image.fromarray(out)

def analyse_all(threshold=15):
    shots = list_screenshots()
    if len(shots) < 2:
        print("Need at least 2 screenshots."); return
    for i in range(len(shots)-1):
        name = f"{shots[i].stem}__{shots[i+1].stem}.png"
        glitch_path = GLITCH_DIR / name
        mask_path = MASK_DIR / name.replace(".png","_mask.png")
        if glitch_path.exists() and mask_path.exists():
            continue
        A, B = Image.open(shots[i]), Image.open(shots[i+1])
        mask, A_aligned, B_aligned = compute_mask(A, B, threshold)
        # save mask (white=changed)
        Image.fromarray(mask.astype(np.uint8)*255).save(mask_path)
        # save glitch
        glitch_img = make_glitch(A_aligned, B_aligned, mask)
        glitch_img.save(glitch_path)
        print("Saved", glitch_path.name)

if __name__=="__main__":
    analyse_all()
