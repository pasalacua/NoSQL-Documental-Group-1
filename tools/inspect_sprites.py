
from PIL import Image, ImageDraw
from pathlib import Path

# Ruta de la spritesheet del protagonista
source = Path(
    "app/static/assets/characters/Player-Sprites-PKM.png"
)

# Abrimos la imagen original
image = Image.open(source).convert("RGBA")

# Ampliamos sin suavizar los píxeles
scale = 4
image = image.resize(
    (image.width * scale, image.height * scale),
    Image.Resampling.NEAREST
)

draw = ImageDraw.Draw(image)

# Dibujamos una cuadrícula cada 16 píxeles originales
step = 16 * scale

for x in range(0, image.width, step):
    draw.line(
        (x, 0, x, image.height),
        fill=(255, 0, 0, 150),
        width=1
    )
    draw.text((x + 2, 2), str(x // scale), fill="red")

for y in range(0, image.height, step):
    draw.line(
        (0, y, image.width, y),
        fill=(255, 0, 0, 150),
        width=1
    )
    draw.text((2, y + 2), str(y // scale), fill="red")

# Guardamos la imagen auxiliar
output = Path(
    "app/static/assets/characters/Player-Sprites-Grid.png"
)

image.save(output)

print(f"Imagen generada: {output}")
