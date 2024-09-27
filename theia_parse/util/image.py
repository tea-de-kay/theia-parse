from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from theia_parse.types import ImageFormat


def image_to_bytes(image: Image.Image, format: ImageFormat) -> bytes:
    data = BytesIO()
    image.save(data, format)
    data.seek(0)

    return data.read()


def caption_image(image: Image.Image, caption: str) -> Image.Image:
    white_section_height = 50
    new_height = image.height + white_section_height
    captioned_image = Image.new("RGB", (image.width, new_height), "white")
    captioned_image.paste(image, (0, 0))
    draw = ImageDraw.Draw(captioned_image)
    font = ImageFont.load_default(size=25)
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_position = (
        (captioned_image.width - text_width) // 2,
        image.height + (white_section_height - text_height) // 2,
    )
    draw.text(text_position, caption, fill="black", font=font)

    return captioned_image
