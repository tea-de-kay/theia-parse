from __future__ import annotations

import hashlib
from functools import cached_property
from uuid import NAMESPACE_OID, uuid5

from pdfplumber.page import Page as PdfPage
from PIL.Image import Image

from theia_parse.model import Medium
from theia_parse.parser.__spi__ import ImageExtractionConfig, ImageSize
from theia_parse.util.image import caption_image


class EmbeddedPdfPageImage:
    def __init__(
        self,
        page: PdfPage,
        raw_image: Image,
        caption_idx: int,
        config: ImageExtractionConfig,
    ) -> None:
        self._page = page
        self._raw_image = raw_image
        self._config = config
        self._caption_idx = caption_idx

    @property
    def caption_idx(self) -> int:
        return self._caption_idx

    @caption_idx.setter
    def caption_idx(self, value: int) -> None:
        self._caption_idx = value

    @property
    def raw_image(self) -> Image:
        return self._raw_image

    @cached_property
    def id(self) -> str:
        digest = hashlib.md5(self.raw_image.tobytes()).digest()

        return str(uuid5(NAMESPACE_OID, digest))

    @property
    def width(self) -> float:
        return self.raw_image.width

    @property
    def height(self) -> float:
        return self.raw_image.height

    @property
    def size(self) -> float:
        return self.width * self.height

    def is_relevant(self, resolution: int | None = None) -> bool:
        if self._config.min_size is not None and self.is_smaller_than(
            self._config.min_size, resolution
        ):
            return False

        if self._config.max_size is not None and self.is_larger_than(
            self._config.max_size, resolution
        ):
            return False

        return True

    def is_smaller_than(self, size: ImageSize, resolution: int | None) -> bool:
        size = size.to_absolute(
            total_width=self._page.width,
            total_height=self._page.height,
            resolution=resolution,
        )
        # TODO: or or and
        if self.width < size.width or self.height < size.height:
            return True

        return False

    def is_larger_than(self, size: ImageSize, resolution: int | None) -> bool:
        size = size.to_absolute(
            total_width=self._page.width,
            total_height=self._page.height,
            resolution=resolution,
        )
        # TODO: or or and
        if self.width > size.width or self.height > size.height:
            return True

        return False

    def to_medium(
        self,
        with_caption: bool = False,
        description: str | None = None,
    ) -> Medium:
        image = self.raw_image
        if with_caption:
            image = caption_image(image, f"image_number = {self.caption_idx}")

        return Medium.create_from_image(
            id=self.id,
            image_format=self._config.image_format,
            raw=image,
            description=description,
        )
