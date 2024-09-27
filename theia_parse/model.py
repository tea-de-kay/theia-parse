from __future__ import annotations

from base64 import b64encode
from enum import StrEnum
from typing import Any

from PIL.Image import Image
from pydantic import BaseModel

from theia_parse.types import ImageFormat
from theia_parse.util.image import image_to_bytes


class LlmUsage(BaseModel):
    request_tokens: int | None = None
    response_tokens: int | None = None
    total_tokens: int | None = None


class ContentType(StrEnum):
    HEADING_1 = "heading-level-1"
    HEADING_2 = "heading-level-2"
    HEADING_3 = "heading-level-3"
    HEADING_4 = "heading-level-4"
    HEADING_5 = "heading-level-5"
    HEADING_6 = "heading-level-6"
    HEADING_7 = "heading-level-7"
    HEADING_8 = "heading-level-8"
    HEADING_9 = "heading-level-9"
    HEADING_10 = "heading-level-10"
    TEXT = "text"
    FOOTER = "footer"
    TABLE = "table"
    TABLE_OF_CONTENTS = "table-of-contents"
    IMAGE = "image"


class ContentElement(BaseModel):
    type: ContentType
    content: str
    medium_id: str | None = None

    @property
    def is_heading(self) -> bool:
        return self.type.value.startswith("heading")

    @property
    def heading_level(self) -> int:
        if not self.is_heading:
            return 0
        else:
            try:
                level = int(self.type.value.split("-")[-1])
            except Exception:
                level = 0

            return level


class Medium(BaseModel):
    id: str
    mime_type: str
    content_b64: str

    @staticmethod
    def create_from_image(id: str, image_format: ImageFormat, raw: Image) -> Medium:
        data = image_to_bytes(raw, image_format)
        mime_type = f"image/{format}"
        return Medium(
            id=id, mime_type=mime_type, content_b64=b64encode(data).decode("utf-8")
        )


class DocumentPage(BaseModel):
    page_nr: int
    content: list[ContentElement]
    media: list[Medium] = []
    raw_extracted: str
    raw_parsed: str
    token_usage: LlmUsage
    metadata: dict[str, Any] = {}
    error: bool = False

    def content_to_string(self) -> str:
        if self.content:
            return str([e.model_dump(mode="json") for e in self.content])
        else:
            return ""

    def get_headings(self) -> list[ContentElement]:
        return [e for e in self.content if e.is_heading]


class ParsedDocument(BaseModel):
    path: str
    md5_sum: str | None = None
    content: list[DocumentPage]
    metadata: dict[str, Any] = {}

    @property
    def token_usage(self) -> LlmUsage:
        request_tokens = 0
        response_tokens = 0
        for element in self.content:
            request_tokens += element.token_usage.request_tokens or 0
            response_tokens += element.token_usage.response_tokens or 0

        return LlmUsage(request_tokens=request_tokens, response_tokens=response_tokens)
