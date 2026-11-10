from PIL import Image, ImageDraw
from pathlib import Path

source = Path("app/static/assets/intro/Intro-Screens-PKM.png")
image = Image.open(source).convert("RGBA")

scale = 5
image = image.resize(
    (image.width * scale, image.height * scale),
    Image.Resampling.NEAREST
)

draw = ImageDraw.Draw(image)

step = 10 * scale

for x in range(0, image.width, step):
    draw.line((x, 0, x, image.height), fill="red", width=1)
    draw.text((x + 2, 2), str(x // scale), fill="red")

for y in range(0, image.height, step):
    draw.line((0, y, image.width, y), fill="red", width=1)
    draw.text((2, y + 2), str(y // scale), fill="red")

output = Path("app/static/assets/intro/Intro-Oak-Grid.png")
image.save(output)

print(f"Imagen generada: {output}")