from abc import ABC, abstractmethod
from pathlib import Path

from pdfplumber.page import Page

from theia_parse.parser.__spi__ import ImageExtractionConfig
from theia_parse.parser.file_parser.pdf.embedded_pdf_page_image import (
    EmbeddedPdfPageImage,
)


class ImageExtractor(ABC):
    def __init__(self, config: ImageExtractionConfig) -> None:
        self._config = config

    @abstractmethod
    def extract(self, path: Path, page: Page) -> list[EmbeddedPdfPageImage]:
        pass
