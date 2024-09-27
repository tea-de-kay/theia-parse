import hashlib
from collections.abc import Iterable
from functools import cached_property
from io import BytesIO
from pathlib import Path
from uuid import NAMESPACE_OID, uuid5

import pdfplumber
from pdfplumber.page import Page as PdfPage
from PIL import Image, ImageDraw, ImageFont

from theia_parse.llm.__spi__ import LLM, PromptAdditions
from theia_parse.model import DocumentPage, Medium, ParsedDocument
from theia_parse.parser.__spi__ import DocumentParserConfig, ImageExtractionConfig
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.util.files import get_md5_sum
from theia_parse.util.image import caption_image
from theia_parse.util.log import LogFactory


RESOLUTION = 200
LAST_HEADINGS_N = 10


_log = LogFactory.get_logger()


class PdfPageEmbeddedImage:
    def __init__(self, page: PdfPage, idx: int, config: ImageExtractionConfig) -> None:
        self._page = page
        self._idx = idx
        self._img_spec = page.images[idx]
        self._config = config

    @cached_property
    def raw_image(self) -> Image.Image:
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
            image = caption_image(image, f"Image Number {self._idx}")

        return Medium.create_from_image(
            id=self.id, image_format=self._config.image_format, raw=image
        )


class PDFParser(FileParser):
    def parse_paged(
        self,
        path: Path,
        llm: LLM,
        config: DocumentParserConfig,
    ) -> Iterable[ParsedDocument | None]:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page.close()

        prompt_additions = PromptAdditions(
            system_prompt_preamble=config.system_prompt_preamble,
            custom_instructions=config.custom_instructions,
        )
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
                page_nr=pdf_page.page_number,
                content=result.content,
                raw_parsed=result.raw,
                raw_extracted=raw_extracted_text,
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

    def _parse_page(self, page: PdfPage, config: DocumentParserConfig) -> DocumentPage:
        image_config = config.image_extraction_config
        full_page_image = Medium.create_from_image(
            id="dummy",
            image_format=image_config.image_format,
            raw=page.to_image(resolution=image_config.resolution).original,
        )

        # TODO: use better parser
        raw_extracted_text = page.extract_text()
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
            page_nr=pdf_page.page_number,
            content=result.content,
            raw_parsed=result.raw,
            raw_extracted=raw_extracted_text,
            token_usage=result.usage,
            error=result.error,
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
