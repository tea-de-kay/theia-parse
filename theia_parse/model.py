from __future__ import annotations

from base64 import b64encode
from enum import StrEnum
from typing import Any

from PIL.Image import Image
from pydantic import BaseModel, computed_field

from theia_parse.types import ImageFormat
from theia_parse.util.image import image_to_bytes
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


class LlmUsage(BaseModel):
    request_tokens: int | None = None
    response_tokens: int | None = None
    total_tokens: int | None = None
    model: str | None = None

    def __add__(self, other: LlmUsage) -> LlmUsage:
        request_tokens = None
        if self.request_tokens is not None or other.request_tokens is not None:
            request_tokens = (self.request_tokens or 0) + (other.request_tokens or 0)

        response_tokens = None
        if self.response_tokens is not None or other.response_tokens is not None:
            request_tokens = (self.response_tokens or 0) + (other.response_tokens or 0)

        total_tokens = None
        if self.total_tokens is not None or other.total_tokens is not None:
            request_tokens = (self.total_tokens or 0) + (other.total_tokens or 0)

        return LlmUsage(
            request_tokens=request_tokens,
            response_tokens=response_tokens,
            total_tokens=total_tokens,
            model=self.model or other.model,
        )

    def __iadd__(self, other: LlmUsage) -> LlmUsage:
        _sum = self + other
        self.request_tokens = _sum.request_tokens
        self.response_tokens = _sum.response_tokens
        self.total_tokens = _sum.total_tokens
        self.model = _sum.model

        return self


class ContentType(StrEnum):
    HEADING = "heading"
    TEXT = "text"
    FOOTER = "footer"
    TABLE = "table"
    TABLE_OF_CONTENTS = "table-of-contents"
    IMAGE = "image"


class RawContentElement(BaseModel):
    type: ContentType
    content: str
    heading_level: int | None = None
    image_number: int | None = None

    def to_element(self, img_nr_to_id: dict[int, str] | None = None) -> ContentElement:
        if self.type == ContentType.HEADING:
            assert self.heading_level is not None
            return HeadingElement(
                content=self.content, heading_level=self.heading_level
            )

        if self.type == ContentType.IMAGE:
            medium_id = None
            if img_nr_to_id is not None and self.image_number is not None:
                medium_id = img_nr_to_id.get(self.image_number)
                if medium_id is None:
                    _log.warning(
                        "Medium could not be matched to embedded image "
                        "[img_nr_to_id={}, image_nr={}]",
                        img_nr_to_id,
                        self.image_number,
                    )

            return ImageElement(content=self.content, medium_id=medium_id)

        return ContentElement(type=self.type, content=self.content)


class ContentElement(BaseModel):
    type: ContentType
    content: str


class HeadingElement(ContentElement):
    type: ContentType = ContentType.HEADING
    heading_level: int


class ImageElement(ContentElement):
    type: ContentType = ContentType.IMAGE
    medium_id: str | None


class Medium(BaseModel):
    id: str
    mime_type: str
    content_b64: str
    description: str | None = None

    @staticmethod
    def create_from_image(
        id: str,
        image_format: ImageFormat,
        raw: Image,
        description: str | None = None,
    ) -> Medium:
        data = image_to_bytes(raw, image_format)
        mime_type = f"image/{image_format}"
        return Medium(
            id=id,
            mime_type=mime_type,
            content_b64=b64encode(data).decode("utf-8"),
            description=description,
        )


class DocumentPage(BaseModel):
    page_number: int
    content: list[ContentElement | HeadingElement | ImageElement]
    media: list[Medium] = []
    raw_extracted_text: str
    raw_llm_response: str
    token_usage: LlmUsage
    metadata: dict[str, Any] = {}
    error: bool = False

    def content_to_string(self) -> str:
        # TODO: use template / better representation
        if self.content:
            return str([e.model_dump(mode="json") for e in self.content])
        else:
            return ""

    def get_headings(self) -> list[HeadingElement]:
        return [e for e in self.content if isinstance(e, HeadingElement)]


class ParsedDocument(BaseModel):
    path: str
    md5_sum: str | None = None
    content: list[DocumentPage]
    metadata: dict[str, Any] = {}

    @computed_field
    @property
    def token_usage(self) -> LlmUsage:
        request_tokens = 0
        response_tokens = 0
        for element in self.content:
            request_tokens += element.token_usage.request_tokens or 0
            response_tokens += element.token_usage.response_tokens or 0

        model = self.content[0].token_usage.model if self.content else None

        return LlmUsage(
            request_tokens=request_tokens, response_tokens=response_tokens, model=model
        )
