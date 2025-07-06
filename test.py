# Playing around with ImageChops to show the difference between two images

from PIL import Image, ImageChops

img1 = Image.open("media/imageA.jpg").convert("RGB")
img2 = Image.open("media/imageB.jpg").convert("RGB")

diff = ImageChops.difference(img1, img2)

output_path = "media/difference.png"
diff.save(output_path)

diff.show()