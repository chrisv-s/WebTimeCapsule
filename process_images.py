# src/process_image.py
from pathlib import Path
from PIL import Image
import numpy as np

# directories for input and output
SCREENSHOT_DIR = Path("media/screenshots")   # raw screenshots from Playwright
GLITCH_DIR = Path("media/glitches")          # colorful glitch effects
MASK_DIR = Path("media/masks")               # black & white difference masks

for d in (GLITCH_DIR, MASK_DIR):
    d.mkdir(parents=True, exist_ok=True)

def list_screenshots():
    return sorted(SCREENSHOT_DIR.glob("*.png"))

# this function concerts the Pillow image to Numpy array
def to_rgb_array(img: Image.Image):
    return np.asarray(img.convert("RGB"), dtype=np.uint8)

def center_crop(a: Image.Image, b: Image.Image):
    """
    Crops both images to the same center size because different screenshots might have slightly different sizes.
    """
    wa, ha = a.size; wb, hb = b.size
    w, h = min(wa, wb), min(ha, hb)  # picks the smaller width/height

    def crop(img):
        W, H = img.size
        left, top = (W - w)//2, (H - h)//2  # this crops around the center
        return img.crop((left, top, left + w, top + h))

    return crop(a), crop(b)


def compute_mask(img_a, img_b, threshold=15):
    """
    This function compares the two images and returns:
      - mask (True where pixels differ more than `threshold`)
    The mask is a boolean array (same size as the images).
    """
    a, b = center_crop(img_a, img_b)
    arr_a, arr_b = to_rgb_array(a).astype(int), to_rgb_array(b).astype(int)

    diff = np.abs(arr_a - arr_b).max(axis=2)

    # marks a change / adds to mask if difference > threshold
    mask = diff > threshold
    return mask, a, b


def shift(channel, dy=0, dx=0):
    """
    This shifts the 2D array (image channel) up/down (dy) or left/right (dx) to create the RGB glitch offset effect.
    """
    out = channel.copy()
    h, w = out.shape

    # vertical shift
    if dy > 0:
        out[dy:,:] = out[:-dy,:]; out[:dy,:] = out[dy:dy+1,:]
    elif dy < 0:
        k = -dy
        out[:-k,:] = out[k:,:]; out[-k:,:] = out[-k-1:-k,:]

    # horizontal shift
    if dx > 0:
        out[:,dx:] = out[:,:-dx]; out[:,:dx] = out[:,dx:dx+1]
    elif dx < 0:
        k = -dx
        out[:,:-k] = out[:,k:]; out[:,-k:] = out[:,-k-1:-k]

    return out


def make_glitch(img_a, img_b, mask):
    """
    This builds a glitch effect from two aligned images using the mask.
    - It starts building from image B and for changed pixels (mask==True), replaces with RGB channel shifts
      that mix A and B together.
    """
    arr_a = to_rgb_array(img_a)
    arr_b = to_rgb_array(img_b)

    # split into channels
    r_a, g_a, b_a = arr_a[...,0], arr_a[...,1], arr_a[...,2]
    r_b, g_b, b_b = arr_b[...,0], arr_b[...,1], arr_b[...,2]

    # shifted versions of A
    r_a_s = shift(r_a, dx=-10)
    g_a_s = shift(g_a, dy=10)
    b_a_s = shift(b_a, dx=10)

    # shifted versions of B
    r_b_s = shift(r_b, dx=10)
    g_b_s = shift(g_b, dy=10)
    b_b_s = shift(b_b, dx=10)

    # starts from B as base
    out = arr_b.copy()

    # This mixes the shifted A and B channels only where mask==True
    out[...,0][mask] = ((r_a_s[mask] + r_b_s[mask]) // 2).astype(np.uint8)
    out[...,1][mask] = ((g_a_s[mask] + g_b_s[mask]) // 2).astype(np.uint8)
    out[...,2][mask] = ((b_a_s[mask] + b_b_s[mask]) // 2).astype(np.uint8)

    return Image.fromarray(out)


def analyse_all(threshold=15):
    """
    This is the main function:
    - Gooes through each pair of consecutive screenshots
    - Computes mask (differences)
    - Saves mask (black & white)
    - Saves glitch (colorful effect)
    """
    shots = list_screenshots()
    if len(shots) < 2:
        print("Need at least 2 screenshots.")
        return

    for i in range(len(shots)-1):
        name = f"{shots[i].stem}__{shots[i+1].stem}.png"
        glitch_path = GLITCH_DIR / name
        mask_path = MASK_DIR / name.replace(".png","_mask.png")

        if glitch_path.exists() and mask_path.exists():
            continue

        # 1. opens both screenshots
        A, B = Image.open(shots[i]), Image.open(shots[i+1])

        # 2. computes mask + aligned images
        mask, A_aligned, B_aligned = compute_mask(A, B, threshold)

        # 3. saves mask (white = changed pixels, black = unchanged)
        Image.fromarray(mask.astype(np.uint8)*255).save(mask_path)

        # 4. saves glitch effect
        glitch_img = make_glitch(A_aligned, B_aligned, mask)
        glitch_img.save(glitch_path)

        print("Saved", glitch_path.name)


if __name__=="__main__":
    analyse_all()
