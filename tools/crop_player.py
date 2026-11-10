
from PIL import Image
from pathlib import Path

source = Path(
    "app/static/assets/characters/Player-Sprites-PKM.png"
)

output = Path(
    "app/static/assets/characters/trainers/Player-idle.png"
)

# Abrimos el spritesheet original, sin modificarlo
image = Image.open(source).convert("RGBA")

# Coordenadas del recorte que habíamos identificado
player = image.crop((85, 120, 100, 138))

# La spritesheet usa naranja para las celdas sin contenido. Se elimina solo
# ese color de fondo; los contornos negros y los tonos de piel permanecen.
background = (248, 120, 40)
pixels = player.load()
for y in range(player.height):
    for x in range(player.width):
        red, green, blue, alpha = pixels[x, y]
        if abs(red - background[0]) <= 8 and abs(green - background[1]) <= 8 and abs(blue - background[2]) <= 8:
            pixels[x, y] = (red, green, blue, 0)

# Ampliamos el sprite sin suavizar los píxeles
scale = 24
player = player.resize(
    (player.width * scale, player.height * scale),
    Image.Resampling.NEAREST
)

output.parent.mkdir(parents=True, exist_ok=True)
player.save(output)

print(f"Sprite limpio generado: {output}")
print(f"Dimensiones: {player.size}")

