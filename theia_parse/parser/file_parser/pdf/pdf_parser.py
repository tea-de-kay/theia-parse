from collections import deque
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pdf2image
import pdfplumber
from pdfplumber.page import Page as PdfPage

from theia_parse.llm.__spi__ import (
    LlmApiSettings,
    LlmGenerationConfig,
    LlmMedium,
    LlmResponse,
    Prompt,
    PromptAdditions,
)
from theia_parse.llm.prompt_templates import (
    PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE,
    PDF_EXTRACT_CONTENT_USER_PROMPT_TEMPLATE,
    PDF_IMPROVE_SYSTEM_PROMPT_TEMPLATE,
    PDF_IMPROVE_USER_PROMPT_TEMPLATE,
    PDF_USER_PARSE_RAW,
)
from theia_parse.llm.response_parser.json_parser import JsonParser
from theia_parse.model import (
    ContentElement,
    DocumentPage,
    HeadingElement,
    ImageElement,
    LlmUsage,
    Medium,
    ParsedDocument,
    RawContentElement,
)
from theia_parse.parser.__spi__ import DocumentParserConfig
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.parser.file_parser.pdf.embedded_pdf_page_image import (
    EmbeddedPdfPageImage,
)
from theia_parse.parser.file_parser.pdf.image_extractor.__spi__ import ImageExtractor
from theia_parse.util.files import get_md5_sum
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


class PdfParser(FileParser):
    def __init__(self, llm_api_settings: LlmApiSettings) -> None:
        super().__init__(llm_api_settings)
        self._system_prompt_extraction = Prompt(
            PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE
        )
        self._user_prompt_extraction = Prompt(PDF_EXTRACT_CONTENT_USER_PROMPT_TEMPLATE)
        self._system_prompt_improve = Prompt(PDF_IMPROVE_SYSTEM_PROMPT_TEMPLATE)
        self._user_prompt_improve = Prompt(PDF_IMPROVE_USER_PROMPT_TEMPLATE)
        self._user_prompt_parse_raw = Prompt(PDF_USER_PARSE_RAW)
        self._json_parser = JsonParser()
        self._image_extractor: ImageExtractor

    def _init_parse(self, config: DocumentParserConfig) -> None:
        if config.image_extraction_config.extract_images:
            if config.image_extraction_config.method == "yodocus":
                from theia_parse.parser.file_parser.pdf.image_extractor.yodocus_image_extractor import (
                    YodocusImageExtractor,
                )

                self._image_extractor = YodocusImageExtractor(
                    config.image_extraction_config
                )
            else:
                from theia_parse.parser.file_parser.pdf.image_extractor.pymupdf_image_extractor import (
                    PymupdfImageExtractor,
                )

                self._image_extractor = PymupdfImageExtractor(
                    config.image_extraction_config
                )

    def parse(self, path: Path, config: DocumentParserConfig) -> ParsedDocument:
        self._init_parse(config)

        doc = self.parse_hull(path)
        doc.content = [
            page for page in self.parse_paged(path, config) if page is not None
        ]

        return doc

    def parse_paged(
        self,
        path: Path,
        config: DocumentParserConfig,
    ) -> Iterable[DocumentPage | None]:
        self._init_parse(config)

        headings: deque[HeadingElement] = deque(
            maxlen=config.prompt_config.consider_last_headings_n
        )
        parsed_pages: deque[DocumentPage] = deque(
            maxlen=config.prompt_config.consider_last_parsed_pages_n
        )

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parsed_page = self._parse_page(
                    path, page, headings, parsed_pages, config
                )
                if parsed_page is not None:
                    headings.extend(parsed_page.get_headings())
                    parsed_pages.append(parsed_page)

                yield parsed_page
                page.close()

    def _parse_page(
        self,
        path: Path,
        page: PdfPage,
        headings: deque[HeadingElement],
        parsed_pages: deque[DocumentPage],
        config: DocumentParserConfig,
    ) -> DocumentPage | None:
        page_image, embedded_images = self._get_images(path, page, config)

        usage = LlmUsage()

        raw_extracted_text, raw_usage = self._parse_raw(page, page_image, config)
        usage += raw_usage

        response = self._call_llm(
            config=config,
            raw_extracted_text=raw_extracted_text,
            headings=headings,
            parsed_pages=parsed_pages,
            page_image=page_image,
            embedded_images=[
                img.to_medium(description=f"image_number = {img.caption_idx}:")
                for img in embedded_images
            ],
        )
        if response is None:
            return

        usage += response.usage

        if config.post_improve:
            improved = self._improve_parsed(
                config=config,
                raw_parsed=response.raw,
                raw_extracted_text=raw_extracted_text,
                page_image=page_image,
            )
            if improved is not None:
                usage += improved.usage
                response = improved

        parsed_response = self._json_parser.parse(response.raw)
        if parsed_response is None:
            return

        content_blocks = parsed_response.get("page_content_blocks")
        if content_blocks is None:
            return

        content, error = self._get_content_list(content_blocks, embedded_images)

        content, media = self._post_process(content, embedded_images)

        return DocumentPage(
            page_number=page.page_number,
            content=content,
            media=media,
            raw_llm_response=response.raw,
            raw_extracted_text=raw_extracted_text,
            token_usage=usage,
            error=error,
        )

    def parse_hull(self, path: Path) -> ParsedDocument:
        md5_sum = get_md5_sum(path)
        with pdfplumber.open(path) as pdf:
            metadata = pdf.metadata

        return ParsedDocument(
            path=str(path), content=[], md5_sum=md5_sum, metadata=metadata
        )

    def get_number_of_pages(self, path: Path, config: DocumentParserConfig) -> int:
        try:
            pdf = pdfplumber.open(path)
            return len(pdf.pages)
        except Exception:
            _log.error("Could not open pdf [path='{0}']", path)

        return 0

    def _call_llm(
        self,
        config: DocumentParserConfig,
        raw_extracted_text: str,
        headings: deque[HeadingElement],
        parsed_pages: deque[DocumentPage],
        page_image: Medium | None,
        embedded_images: list[Medium],
    ) -> LlmResponse | None:
        image_config = config.image_extraction_config

        prompt_additions = PromptAdditions.create(
            config=config,
            raw_extracted_text=raw_extracted_text,
            previous_headings=headings,
            previous_parsed_pages=parsed_pages,
            embedded_images=embedded_images,
        )

        system_prompt = self._system_prompt_extraction.render(
            prompt_additions.to_dict()
        )
        user_prompt = self._user_prompt_extraction.render(prompt_additions.to_dict())
        images = [
            LlmMedium(
                image=img,
                detail_level="low" if image_config.use_low_details else "auto",
                description=img.description,
            )
            for img in embedded_images
        ]

        return self._llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            page_image=(
                LlmMedium(image=page_image, description=page_image.description)
                if page_image is not None
                else None
            ),
            embedded_images=images,
            config=LlmGenerationConfig(),
        )

    def _improve_parsed(
        self,
        config: DocumentParserConfig,
        raw_parsed: str,
        raw_extracted_text: str,
        page_image: Medium | None,
    ) -> LlmResponse | None:
        prompt_additions = PromptAdditions.create(
            config=config,
            raw_extracted_text=raw_extracted_text,
            raw_parsed=raw_parsed,
        )

        system_prompt = self._system_prompt_improve.render(prompt_additions.to_dict())
        user_prompt = self._user_prompt_improve.render(prompt_additions.to_dict())

        return self._llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            page_image=(
                LlmMedium(image=page_image, description=page_image.description)
                if page_image is not None
                else None
            ),
            embedded_images=[],
            config=LlmGenerationConfig(),
        )

    def _get_content_list(
        self,
        raw_blocks: list[dict[str, Any]],
        embedded_images: list[EmbeddedPdfPageImage],
    ) -> tuple[list[ContentElement], bool]:
        img_nr_to_id = {img.caption_idx: img.id for img in embedded_images}
        error = False
        elements: list[ContentElement] = []
        for block in raw_blocks:
            try:
                raw = RawContentElement(**block)
                elements.append(raw.to_element(img_nr_to_id))
            except Exception as e:
                _log.error(
                    "Raw block {0}, could not be converted to a content element: {1}",
                    block,
                    e,
                )
                error = True

        return elements, error

    def _post_process(
        self,
        content: list[ContentElement],
        embedded_images: list[EmbeddedPdfPageImage],
    ) -> tuple[list[ContentElement], list[Medium]]:
        id_to_img = {img.id: img for img in embedded_images}
        media: list[Medium] = []
        for element in content:
            if isinstance(element, ImageElement) and element.medium_id is not None:
                img = id_to_img.get(element.medium_id)
                if img is not None:
                    media.append(img.to_medium(description=element.content))
                else:
                    element.medium_id = None

        return content, media

    def _get_images(
        self,
        path: Path,
        page: PdfPage,
        config: DocumentParserConfig,
    ) -> tuple[Medium | None, list[EmbeddedPdfPageImage]]:
        if not config.use_vision:
            return None, []

        image_config = config.image_extraction_config
        full_page_image = Medium.create_from_image(
            id="",
            image_format=image_config.image_format,
            raw=pdf2image.convert_from_path(
                path,
                dpi=image_config.resolution,
                first_page=page.page_number,
                last_page=page.page_number,
            )[0],
            description="Image of the full PDF page:",
        )

        if not image_config.extract_images:
            return full_page_image, []

        embedded_images = self._image_extractor.extract(path, page)

        return full_page_image, embedded_images

    def _parse_raw(
        self,
        page: PdfPage,
        page_image: Medium | None,
        config: DocumentParserConfig,
    ) -> tuple[str, LlmUsage]:
        raw = page.extract_text()
        usage = LlmUsage()
        if config.raw_parser_config.parser_type == "llm":
            prompt_additions = PromptAdditions.create(
                config=config,
                raw_extracted_text=raw,
            )

            user_prompt = self._user_prompt_parse_raw.render(prompt_additions.to_dict())

            response = self._llm.generate(
                system_prompt=None,
                user_prompt=user_prompt,
                page_image=(
                    LlmMedium(image=page_image, description=page_image.description)
                    if page_image is not None
                    else None
                ),
                embedded_images=[],
                config=LlmGenerationConfig(json_mode=False),
            )

            if response is not None:
                raw = response.raw
                usage = response.usage

        return raw, usage
