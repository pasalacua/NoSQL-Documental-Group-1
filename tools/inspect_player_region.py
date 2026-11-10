from PIL import Image, ImageDraw

source = "app/static/assets/characters/Player-Sprites-PKM.png"
output = "app/static/assets/characters/Player-Detail.png"

image = Image.open(source).convert("RGBA")

# Recorte de la zona identificada
image = image.crop((85, 120, 100, 138))

scale = 24
image = image.resize(
    (image.width * scale, image.height * scale),
    Image.Resampling.NEAREST
)

draw = ImageDraw.Draw(image)

for x in range(0, image.width, scale):
    draw.line((x, 0, x, image.height), fill="red", width=1)

for y in range(0, image.height, scale):
    draw.line((0, y, image.width, y), fill="red", width=1)

image.save(output)
print(f"Imagen generada: {output}")