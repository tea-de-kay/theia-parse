from collections import deque
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Deque

import pdfplumber
from pdfplumber.page import Page as PdfPage

from theia_parse.llm.__spi__ import (
    LlmApiSettings,
    LlmGenerationConfig,
    LlmResponse,
    Prompt,
    PromptAdditions,
)
from theia_parse.llm.prompt_templates import (
    PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE,
    PDF_EXTRACT_CONTENT_USER_PROMPT_TEMPLATE,
)
from theia_parse.llm.response_parser.json_parser import JsonParser
from theia_parse.model import (
    ContentElement,
    DocumentPage,
    HeadingElement,
    ImageElement,
    Medium,
    ParsedDocument,
    RawContentElement,
)
from theia_parse.parser.__spi__ import DocumentParserConfig, PromptConfig
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.parser.file_parser.pdf.embedded_pdf_page_image import (
    EmbeddedPdfPageImage,
)
from theia_parse.util.files import get_md5_sum
from theia_parse.util.log import LogFactory


IMAGE_NUMBER_PATTERN = r"\s*image_number\s*=\s*(\d+)\s*(.*)"


_log = LogFactory.get_logger()


class PdfParser(FileParser):
    def __init__(self, llm_api_settings: LlmApiSettings) -> None:
        super().__init__(llm_api_settings)
        self._system_prompt = Prompt(PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE)
        self._user_prompt = Prompt(PDF_EXTRACT_CONTENT_USER_PROMPT_TEMPLATE)
        self._json_parser = JsonParser()

    def parse(self, path: Path, config: DocumentParserConfig) -> ParsedDocument:
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
        headings: Deque[HeadingElement] = deque(
            maxlen=config.prompt_config.consider_last_headings_n
        )
        parsed_pages: Deque[DocumentPage] = deque(
            maxlen=config.prompt_config.consider_last_parsed_pages_n
        )

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parsed_page = self._parse_page(page, headings, parsed_pages, config)
                if parsed_page is not None:
                    headings.extend(parsed_page.get_headings())
                    parsed_pages.append(parsed_page)

                yield parsed_page
                page.close()

    def _parse_page(
        self,
        page: PdfPage,
        headings: Deque[HeadingElement],
        parsed_pages: Deque[DocumentPage],
        config: DocumentParserConfig,
    ) -> DocumentPage | None:
        page_image, embedded_images = self._get_images(page, config)

        # TODO: use better parser
        raw_extracted_text = page.extract_text()

        response = self._call_llm(
            config=config.prompt_config,
            raw_extracted_text=raw_extracted_text,
            headings=headings,
            parsed_pages=parsed_pages,
            page_image=page_image,
            embedded_images=[
                img.to_medium(with_caption=True) for img in embedded_images
            ],
        )
        if response is None:
            return

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
            token_usage=response.usage,
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
        config: PromptConfig,
        raw_extracted_text: str,
        headings: Deque[HeadingElement],
        parsed_pages: Deque[DocumentPage],
        page_image: Medium | None,
        embedded_images: list[Medium],
    ) -> LlmResponse | None:
        prompt_additions = PromptAdditions.create(
            config=config,
            raw_extracted_text=raw_extracted_text,
            previous_headings=headings,
            previous_parsed_pages=parsed_pages,
            embedded_images=embedded_images,
        )

        system_prompt = self._system_prompt.render(prompt_additions.to_dict())
        user_prompt = self._user_prompt.render(prompt_additions.to_dict())
        images = embedded_images
        if page_image is not None:
            images = [page_image] + images

        return self._llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            images=images,
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
            if isinstance(element, ImageElement):
                if element.medium_id is not None:
                    img = id_to_img.get(element.medium_id)
                    if img is not None:
                        media.append(img.to_medium(description=element.content))
                    else:
                        element.medium_id = None

        return content, media

    def _get_images(
        self,
        page: PdfPage,
        config: DocumentParserConfig,
    ) -> tuple[Medium | None, list[EmbeddedPdfPageImage]]:
        if not config.use_vision:
            return None, []

        image_config = config.image_extraction_config
        full_page_image = Medium.create_from_image(
            id="",
            image_format=image_config.image_format,
            raw=page.to_image(resolution=image_config.resolution).original,
        )

        if not image_config.extract_images:
            return full_page_image, []

        embedded_images: list[EmbeddedPdfPageImage] = []
        caption_idx = 1
        for img_spec in page.images:
            img = EmbeddedPdfPageImage(
                page=page,
                image_spec=img_spec,
                caption_idx=caption_idx,
                config=image_config,
            )
            if img.is_relevant:
                embedded_images.append(img)
                caption_idx += 1

        if image_config.exclude_fully_contained:
            filtered = []
            for ei in embedded_images:
                checks = [check for check in embedded_images if check is not ei]
                if not any(ei.is_contained(check) for check in checks):
                    filtered.append(ei)
            embedded_images = filtered

        return full_page_image, embedded_images
