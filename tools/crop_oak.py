from PIL import Image

source = "app/static/assets/intro/Intro-Screens-PKM.png"
output = "app/static/assets/characters/trainers/professor-oak.png"

image = Image.open(source).convert("RGBA")

# Recortar al Profesor Oak
oak = image.crop((5, 170, 60, 256))

oak.save(output)

print(f"Profesor Oak guardado en: {output}")
print(f"Dimensiones: {oak.size}")