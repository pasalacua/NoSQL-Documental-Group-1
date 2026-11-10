
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

