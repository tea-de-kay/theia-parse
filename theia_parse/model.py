from enum import Enum

from pydantic import BaseModel


class ContentType(Enum):
    HEADING_1 = "heading-level-1"
    HEADING_2 = "heading-level-2"
    HEADING_3 = "heading-level-3"
    HEADING_4 = "heading-level-4"
    HEADING_5 = "heading-level-5"
    HEADING_6 = "heading-level-6"
    TEXT = "text"
    FOOTER = "footer"
    TABLE = "table"


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
    error: bool = False

    def to_string(self) -> str:
        if self.content:
            return str([e.model_dump() for e in self.content])
        else:
            return ""

    def get_headings(self) -> list[ContentElement]:
        if self.content:
            return [e for e in self.content if e.is_heading()]
        else:
            return []


class ParsedDocument(BaseModel):
    path: str
    pages: list[DocumentPage]


class PromptAdditions(BaseModel):
    system_preamble: str | None = None
    custom_instructions: list[str] | None = None
    structured_previous_page: str | None = None
    previous_headings: str | None = None
