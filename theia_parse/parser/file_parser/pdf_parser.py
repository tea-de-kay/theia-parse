from io import BytesIO

import pdfplumber
from tqdm import tqdm

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import DocumentPage, ParsedDocument
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.util.log import LogFactory


RESOLUTION = 300
LAST_HEADINGS_N = 10


class PDFParser(FileParser):
    _log = LogFactory.get_logger()

    def parse(self, path: str, llm: LLM, verbose: bool = True) -> ParsedDocument | None:
        try:
            pdf = pdfplumber.open(path)
        except Exception:
            self._log.error("Could not open pdf [path='{0}']", path)

        pages: list[DocumentPage] = []
        for pdf_page in tqdm(pdf.pages) if verbose else pdf.pages:
            img = pdf_page.to_image(resolution=RESOLUTION)
            img_data = BytesIO()
            img.save(img_data)

            raw_extracted_text = pdf_page.extract_text()
            previous_page = pages[-1].to_string() if pages else "no previous page"
            previous_headings = [
                h.model_dump()
                for headings in [e.get_headings() for e in pages]
                for h in headings
            ][-LAST_HEADINGS_N:]
