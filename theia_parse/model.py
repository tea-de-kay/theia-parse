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


class DocumentPage(BaseModel):
    page_nr: int
    elements: list[ContentElement] | None
    raw_parsed: str
    raw_extracted: str

    def to_string(self) -> str:
        if self.elements:
            return f"""{{'page_content': {[e.model_dump() for e in self.elements]}}}"""
        else:
            return ""

    def get_headings(self) -> list[ContentElement]:
        if self.elements:
            return [e for e in self.elements if e.type.value.startswith("heading")]
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
