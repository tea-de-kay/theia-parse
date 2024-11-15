from __future__ import annotations

import hashlib
from functools import cached_property
from typing import Any
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

    @caption_idx.setter
    def caption_idx(self, value: int) -> None:
        self._caption_idx = value

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
    def size(self) -> float:
        return self.width * self.height

    @property
    def is_relevant(self) -> bool:
        if self._config.min_size is not None and self.is_smaller_than(
            self._config.min_size
        ):
            return False

        if self._config.max_size is not None and self.is_larger_than(
            self._config.max_size
        ):
            return False

        return True

    def is_contained(self, image: EmbeddedPdfPageImage) -> bool:
        image_x0, image_top, image_x1, image_bottom = image.bbox
        self_x0, self_top, self_x1, self_bottom = self.bbox

        return (
            image_x0 >= self_x0
            and image_top >= self_top
            and image_x1 <= self_x1
            and image_bottom <= self_bottom
        )

    def is_smaller_than(self, size: ImageSize) -> bool:
        size = size.to_absolute(
            total_width=self._page.width, total_height=self._page.height
        )
        # TODO: or or and
        if self.width < size.width or self.height < size.height:
            return True

        return False

    def is_larger_than(self, size: ImageSize) -> bool:
        size = size.to_absolute(
            total_width=self._page.width, total_height=self._page.height
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
