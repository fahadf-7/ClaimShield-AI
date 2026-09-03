from argparse import ArgumentParser
from pathlib import Path

from PIL import Image, ImageDraw


def generate(output: Path) -> None:
    image = Image.new("RGB", (1000, 700), (224, 232, 238))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((230, 150, 770, 405), radius=42, fill=(20, 155, 105))
    draw.rounded_rectangle((110, 405, 890, 620), radius=35, fill=(25, 95, 210))
    draw.ellipse((315, 475, 455, 575), fill=(220, 35, 55))
    draw.line((540, 455, 745, 555), fill=(245, 125, 25), width=18)
    draw.line((430, 225, 565, 345), fill=(125, 45, 185), width=14)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)


if __name__ == "__main__":
    parser = ArgumentParser(description="Generate the fixed synthetic Phase 1 evaluation image.")
    parser.add_argument("output", type=Path, help="Destination PNG path")
    arguments = parser.parse_args()
    generate(arguments.output)
    print(arguments.output.resolve())
