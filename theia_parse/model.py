from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(StrEnum):
    HEADING_1 = "heading-level-1"
    HEADING_2 = "heading-level-2"
    HEADING_3 = "heading-level-3"
    HEADING_4 = "heading-level-4"
    HEADING_5 = "heading-level-5"
    HEADING_6 = "heading-level-6"
    TEXT = "text"
    FOOTER = "footer"
    TABLE = "table"
    TABLE_OF_CONTENTS = "table-of-contents"
    IMAGE = "image"


class ContentElement(BaseModel):
    type: ContentType
    content: str
    language: str

    def is_heading(self) -> bool:
        return self.type.value.startswith("heading")

    @property
    def heading_level(self) -> int | None:
        if not self.is_heading():
            return
        else:
            return int(self.type.value.split("-")[-1])


class LLMUsage(BaseModel):
    request_tokens: int | None = None
    response_tokens: int | None = None
    total_tokens: int | None = None


class DocumentPage(BaseModel):
    page_nr: int
    content: list[ContentElement] | None
    raw_parsed: str
    raw_extracted: str
    token_usage: LLMUsage
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: bool = False

    def content_to_string(self) -> str:
        if self.content:
            return str([e.model_dump(mode="json") for e in self.content])
        else:
            return ""

    def get_headings(self) -> list[ContentElement]:
        if self.content:
            return [e for e in self.content if e.is_heading()]
        else:
            return []


class ParsedDocument(BaseModel):
    path: str
    md5_sum: str | None = None
    pages: list[DocumentPage]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def token_usage(self) -> LLMUsage:
        request_tokens = 0
        response_tokens = 0
        for page in self.pages:
            request_tokens += page.token_usage.request_tokens or 0
            response_tokens += page.token_usage.response_tokens or 0

        return LLMUsage(request_tokens=request_tokens, response_tokens=response_tokens)
