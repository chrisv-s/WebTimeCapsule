from PIL import Image
import numpy as np

# converting the two images to arrays
img_a = Image.open("imageA.jpg").convert("RGB")
img_b = Image.open("imageB.jpg").convert("RGB")

arr_a = np.array(img_a)
arr_b = np.array(img_b)

# calculating absolute difference
diff = np.abs(arr_a.astype(int) - arr_b.astype(int))

# Here I asked ChatGPT to write me a code that does a "glitch" effect where the images differ
# I wanted to see if my idea made sense???

threshold = 30
mask = np.any(diff > threshold, axis=2)  # 2D mask where any channel is different

# Create output image based on B, and apply glitch only in changed areas
glitched = arr_b.copy()

# RGB Channel shift glitch: swap or shift RGB channels in masked area
r, g, b = arr_b[:, :, 0], arr_b[:, :, 1], arr_b[:, :, 2]

# Example glitch: roll channels in opposite directions (sliced glitchy feel)
r_shift = np.roll(r, shift=5, axis=1)
g_shift = np.roll(g, shift=-5, axis=0)
b_shift = np.roll(b, shift=10, axis=1)

# Apply the glitch only where mask is True
glitched[mask, 0] = r_shift[mask]
glitched[mask, 1] = g_shift[mask]
glitched[mask, 2] = b_shift[mask]

# Convert back to image and save
glitched_img = Image.fromarray(glitched.astype('uint8'))
glitched_img.save("glitched_output.png")
print("✅ Glitched image saved as glitched_output.png")