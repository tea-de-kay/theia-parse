from pydantic import BaseModel

from theia_parse.types import ImageFormat


class ImageSize(BaseModel):
    width: int
    height: int


class ImageExtractionConfig(BaseModel):
    extract_images: bool = True
    min_size: ImageSize | None = ImageSize(width=20, height=20)
    max_size: ImageSize | None = None
    resolution: int = 300
    image_format: ImageFormat = "webp"


class DocumentParserConfig(BaseModel):
    verbose: bool = True
    save_file: bool = True
    system_prompt_preamble: str | None = None
    custom_instructions: list[str] | None = None
    image_extraction_config: ImageExtractionConfig = ImageExtractionConfig()


class DirectoryParserConfig(BaseModel):
    verbose: bool = True
    deduplicate_docs: bool = True
    document_parser_config: DocumentParserConfig = DocumentParserConfig()
