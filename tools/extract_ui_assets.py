from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "static" / "assets"


def extract_assets():
    menu_frames = Image.open(
        ASSETS / "interface" / "Menu-Frames-PKM.png"
    ).convert("RGBA")
    intro_screens = Image.open(
        ASSETS / "intro" / "Intro-Screens-PKM.png"
    ).convert("RGBA")

    output_dir = ASSETS / "interface"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Esquina de un marco azul de Menu-Frames-PKM. Se usa como border-image
    # para que los diálogos mantengan el estilo de Pokémon.
    menu_frames.crop((4, 16, 32, 44)).save(
        output_dir / "dialogue-frame.png"
    )

    # Marco de la caja de nombre de Intro-Screens-PKM.
    intro_screens.crop((4, 428, 32, 456)).save(
        output_dir / "name-frame.png"
    )

    print("Marcos extraídos: dialogue-frame.png y name-frame.png")


if __name__ == "__main__":
    extract_assets()
