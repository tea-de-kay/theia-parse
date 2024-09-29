import hashlib
from functools import cached_property
from typing import Any
from uuid import NAMESPACE_OID, uuid5

from pdfplumber.page import Page as PdfPage
from PIL.Image import Image

from theia_parse.model import Medium
from theia_parse.parser.__spi__ import ImageExtractionConfig
from theia_parse.util.image import caption_image


class EmbeddedPdfPageImage:
    def __init__(
        self,
        page: PdfPage,
        image_spec: dict[str, Any],
        caption_idx: int,
        config: ImageExtractionConfig,
    ) -> None:
        self._page = page
        self._img_spec = image_spec
        self._config = config
        self._caption_idx = caption_idx

    @property
    def caption_idx(self) -> int:
        return self._caption_idx

    @cached_property
    def raw_image(self) -> Image:
        crop = self._page.within_bbox(self.bbox, strict=False)
        image = crop.to_image(resolution=self._config.resolution).original

        return image

    @cached_property
    def id(self) -> str:
        digest = hashlib.md5(self.raw_image.tobytes()).digest()

        return str(uuid5(NAMESPACE_OID, digest))

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (
            self._img_spec["x0"],
            self._img_spec["top"],
            self._img_spec["x1"],
            self._img_spec["bottom"],
        )

    @property
    def width(self) -> float:
        return self._img_spec["x1"] - self._img_spec["x0"]

    @property
    def height(self) -> float:
        return self._img_spec["bottom"] - self._img_spec["top"]

    @property
    def is_relevant(self) -> bool:
        if self._config.min_size is not None:
            if (
                self.width < self._config.min_size.width
                or self.height < self._config.min_size.height
            ):
                return False

        if self._config.max_size is not None:
            if (
                self.width > self._config.max_size.width
                or self.height > self._config.max_size.height
            ):
                return False

        return True

    def to_medium(self, with_caption: bool = False) -> Medium:
        image = self.raw_image
        if with_caption:
            image = caption_image(image, f"image_number = {self.caption_idx}")

        return Medium.create_from_image(
            id=self.id, image_format=self._config.image_format, raw=image
        )
