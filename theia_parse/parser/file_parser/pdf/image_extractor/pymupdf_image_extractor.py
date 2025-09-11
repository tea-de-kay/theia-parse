import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf4llm
from pdfplumber.page import Page
from PIL import Image

from theia_parse.parser.file_parser.pdf.embedded_pdf_page_image import (
    EmbeddedPdfPageImage,
)
from theia_parse.parser.file_parser.pdf.image_extractor.__spi__ import ImageExtractor
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


class PymupdfImageExtractor(ImageExtractor):
    def extract(self, path: Path, page: Page) -> list[EmbeddedPdfPageImage]:
        embedded_images: list[EmbeddedPdfPageImage] = []
        caption_idx = 1

        with TemporaryDirectory() as temp_dir:
            # TODO: use markdown
            pymupdf4llm.to_markdown(
                path,
                pages=[page.page_number - 1],  # pdfplumber 1-based, pymupdf 0-based
                write_images=True,
                image_path=temp_dir,
                table_strategy="",
            )

            for filename in os.listdir(temp_dir):
                image_path = os.path.join(temp_dir, filename)
                try:
                    raw_img = Image.open(image_path)
                except Exception as e:
                    _log.warning("Failed to load image {}: {}", filename, e)
                else:
                    img = EmbeddedPdfPageImage(
                        page=page,
                        raw_image=raw_img,
                        caption_idx=caption_idx,
                        config=self._config,
                    )
                    # TODO: check resolution
                    if img.is_relevant():
                        embedded_images.append(img)
                        caption_idx += 1

        embedded_images = sorted(embedded_images, key=lambda x: x.size, reverse=True)
        embedded_images = embedded_images[: self._config.max_images_per_page]

        for caption_idx, ei in enumerate(embedded_images, start=1):
            ei.caption_idx = caption_idx

        return embedded_images
