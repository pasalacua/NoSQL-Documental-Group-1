from PIL import Image

source = "app/static/assets/intro/Intro-Screens-PKM.png"
output = "app/static/assets/characters/trainers/professor-oak.png"

image = Image.open(source).convert("RGBA")

# Recortar al Profesor Oak
oak = image.crop((5, 170, 60, 256))

# La hoja original usa verde como fondo. Se vuelve transparente sin tocar
# los colores del sprite para que pueda integrarse con el escenario.
background = (8, 120, 8)
pixels = oak.load()
for y in range(oak.height):
    for x in range(oak.width):
        red, green, blue, alpha = pixels[x, y]
        if abs(red - background[0]) <= 8 and abs(green - background[1]) <= 8 and abs(blue - background[2]) <= 8:
            pixels[x, y] = (red, green, blue, 0)

oak.save(output)

print(f"Profesor Oak guardado en: {output}")
print(f"Dimensiones: {oak.size}")
