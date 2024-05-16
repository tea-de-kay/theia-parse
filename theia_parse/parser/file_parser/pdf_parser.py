from io import BytesIO
from pathlib import Path

import pdfplumber
from tqdm import tqdm

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import (
    DocumentPage,
    DocumentParserConfig,
    ParsedDocument,
)
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.util.log import LogFactory


RESOLUTION = 150
LAST_HEADINGS_N = 10


class PDFParser(FileParser):
    _log = LogFactory.get_logger()

    def parse(
        self,
        path: Path,
        llm: LLM,
        config: DocumentParserConfig,
    ) -> ParsedDocument | None:
        try:
            pdf = pdfplumber.open(path)
        except Exception:
            self._log.error("Could not open pdf [path='{0}']", path)
            return

        prompt_additions = config.prompt_additions.model_copy(deep=True)
        pages: list[DocumentPage] = []
        for pdf_page in tqdm(
            pdf.pages,
            disable=not config.verbose,
            desc="pages in file",
            leave=False,
        ):
            # TODO: Every image is resized to 1024x1024
            # Allow for multiple images per page to provide high resolution
            img = pdf_page.to_image(resolution=RESOLUTION)
            img_data = BytesIO()
            img.save(img_data)
            img_data.seek(0)

            # TODO: use better parser and include extracted images
            raw_extracted_text = pdf_page.extract_text()
            previous_headings = [
                h.model_dump()
                for headings in [p.get_headings() for p in pages]
                for h in headings
            ][-LAST_HEADINGS_N:]

            prompt_additions.previous_headings = str(previous_headings)

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

        return ParsedDocument(path=str(path), pages=pages)
