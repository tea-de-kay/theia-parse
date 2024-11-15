from __future__ import annotations

from pydantic import BaseModel

from theia_parse.types import ImageFormat


T_num = int | float


class ImageSize(BaseModel):
    """
    Image size specification
    floats denote relative percentages compared to the full page
    """

    width: T_num
    height: T_num

    def to_absolute(self, total_width: T_num, total_height: T_num) -> ImageSize:
        width = self.width
        if isinstance(self.width, float):
            width = int(self.width * total_width)

        height = self.height
        if isinstance(self.height, float):
            height = int(self.height * total_height)

        return ImageSize(width=width, height=height)


class ImageExtractionConfig(BaseModel):
    extract_images: bool = True
    min_size: ImageSize | None = ImageSize(width=20, height=20)
    max_size: ImageSize | None = ImageSize(width=0.9, height=0.9)

    exclude_fully_contained: bool = True
    """Whether to exclude images which are fully contained in another image"""

    max_images_per_page: int = 10
    """Keep at most the largest N embedded images per page"""

    use_low_details: bool = True
    """Whether to only use a low resolution version for llm inference to save tokens."""

    resolution: int = 300
    image_format: ImageFormat = "webp"


class PromptConfig(BaseModel):
    system_prompt_preamble: str | None = None
    custom_instructions: list[str] | None = None
    consider_last_headings_n: int = 10
    consider_last_parsed_pages_n: int = 0
    include_raw_extracted_text: bool = True


class DocumentParserConfig(BaseModel):
    verbose: bool = True
    save_file: bool = False
    use_vision: bool = True
    post_improve: bool = False
    prompt_config: PromptConfig = PromptConfig()
    image_extraction_config: ImageExtractionConfig = ImageExtractionConfig()


class DirectoryParserConfig(BaseModel):
    verbose: bool = True
    deduplicate_docs: bool = True
    document_parser_config: DocumentParserConfig = DocumentParserConfig()
