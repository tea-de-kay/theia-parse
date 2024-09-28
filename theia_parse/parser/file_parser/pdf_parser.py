import hashlib
from collections import deque
from collections.abc import Iterable
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any, Deque
from uuid import NAMESPACE_OID, uuid5

import pdfplumber
from pdfplumber.page import Page as PdfPage
from PIL.Image import Image

from theia_parse.llm import get_llm
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
from theia_parse.model import ContentElement, DocumentPage, Medium, ParsedDocument
from theia_parse.parser.__spi__ import (
    DocumentParserConfig,
    ImageExtractionConfig,
    PromptConfig,
)
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.util.files import get_md5_sum
from theia_parse.util.image import caption_image
from theia_parse.util.log import LogFactory


RESOLUTION = 200
LAST_HEADINGS_N = 10


_log = LogFactory.get_logger()


class EmbeddedPdfPageImage:
    def __init__(self, page: PdfPage, idx: int, config: ImageExtractionConfig) -> None:
        self._page = page
        self._idx = idx
        self._img_spec = page.images[idx]
        self._config = config

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
    def is_relevant(self) -> bool:
        if self._config.min_size is not None:
            if (
                self.width < self._config.min_size.width
                or self.height < self._config.min_size.height
            ):
                return False

        if self._config.max_size is not None:
            if (
                self.width > self._config.max_size.width
                or self.height > self._config.max_size.height
            ):
                return False

        return True

    def to_medium(self, with_caption: bool) -> Medium:
        image = self.raw_image
        if with_caption:
            image = caption_image(image, f"image_number = {self._idx}")

        return Medium.create_from_image(
            id=self.id, image_format=self._config.image_format, raw=image
        )


class PDFParser(FileParser):
    def __init__(self, llm_api_settings: LlmApiSettings) -> None:
        self._llm = get_llm(llm_api_settings)
        self._system_prompt = Prompt(PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE)
        self._user_prompt = Prompt(PDF_EXTRACT_CONTENT_USER_PROMPT_TEMPLATE)
        self._json_parser = JsonParser()

    def parse_paged(
        self,
        path: Path,
        config: DocumentParserConfig,
    ) -> Iterable[DocumentPage | None]:
        headings: Deque[ContentElement] = deque(
            maxlen=config.prompt_config.consider_last_headings_n
        )
        parsed_pages: Deque[DocumentPage] = deque(
            maxlen=config.prompt_config.consider_last_parsed_pages_n
        )

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                yield self._parse_page(page, headings, parsed_pages, config)
                page.close()

        pages: list[DocumentPage] = []
        for pdf_page in tqdm(
            pdf.pages,
            disable=not config.verbose,
            desc="page in file",
            leave=False,
            ncols=80,
        ):
            # TODO: Every image is resized to 1024x1024 (?)
            # Allow for multiple images per page to provide high resolution
            img = pdf_page.to_image(resolution=RESOLUTION)
            img_data = BytesIO()
            img.save(img_data)
            img_data.seek(0)

            # TODO: use better parser and include extracted images
            raw_extracted_text = pdf_page.extract_text()
            previous_headings = [
                h.model_dump(mode="json")
                for headings in [p.get_headings() for p in pages]
                for h in headings
            ][-LAST_HEADINGS_N:]

            prompt_additions.previous_headings = str(previous_headings)
            prompt_additions.previous_structured_page_content = (
                pages[-1].content_to_string() if pages else None
            )

            result = llm.extract(
                image_data=img_data.read(),
                raw_extracted_text=raw_extracted_text,
                prompt_additions=prompt_additions,
            )

            page = DocumentPage(
                page_number=pdf_page.page_number,
                content=result.content,
                raw_parsed=result.raw,
                raw_extracted_text=raw_extracted_text,
                token_usage=result.usage,
                error=result.error,
            )
            pages.append(page)
            pdf_page.close()

        pdf.close()

        return ParsedDocument(
            path=str(path),
            md5_sum=md5_sum,
            content=pages,
            metadata=metadata,
        )

    def _parse_page(
        self,
        page: PdfPage,
        headings: Deque[ContentElement],
        parsed_pages: Deque[DocumentPage],
        config: DocumentParserConfig,
    ) -> DocumentPage | None:
        page_image, embedded_images = self._get_images(
            page, config.image_extraction_config
        )

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

        content, error = self._get_content_list(content_blocks)

        # result = llm.extract(
        #     image_data=img_data.read(),
        #     raw_extracted_text=raw_extracted_text,
        #     prompt_additions=prompt_additions,
        # )

        # page = DocumentPage(
        #     page_nr=pdf_page.page_number,
        #     content=result.content,
        #     raw_parsed=result.raw,
        #     raw_extracted=raw_extracted_text,
        #     token_usage=result.usage,
        #     error=result.error,
        # )

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
        headings: Deque[ContentElement],
        parsed_pages: Deque[DocumentPage],
        page_image: Medium,
        embedded_images: list[Medium],
    ) -> LlmResponse | None:
        prompt_addtions = PromptAdditions.create(
            config=config,
            raw_extracted_text=raw_extracted_text,
            previous_headings=headings,
            previous_parsed_pages=parsed_pages,
        )

        system_prompt = self._system_prompt.render(prompt_addtions.to_dict())
        user_prompt = self._user_prompt.render(prompt_addtions.to_dict())
        images = [page_image] + embedded_images

        return self._llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            images=images,
            config=LlmGenerationConfig(),
        )

    def _get_content_list(
        self,
        content_blocks: list[dict[str, Any]],
    ) -> tuple[list[ContentElement], bool]:
        error = False
        elements = []
        for block in content_blocks:
            try:
                elements.append(ContentElement(**block))
            except Exception as e:
                _log.error(
                    "Raw block {0}, could not be converted to a content element: {1}",
                    block,
                    e,
                )
                error = True

        return elements, error

    def _get_images(
        self,
        page: PdfPage,
        config: ImageExtractionConfig,
    ) -> tuple[Medium, list[EmbeddedPdfPageImage]]:
        full_page_image = Medium.create_from_image(
            id="dummy",
            image_format=config.image_format,
            raw=page.to_image(resolution=config.resolution).original,
        )
        embedded_images = [
            EmbeddedPdfPageImage(page, idx, config) for idx in range(len(page.images))
        ]

        return full_page_image, embedded_images
