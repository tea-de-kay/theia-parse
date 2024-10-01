from tests.conftest import RESOURCE_PATH
from theia_parse.llm.__spi__ import LlmApiEnvSettings
from theia_parse.parser.__spi__ import DocumentParserConfig
from theia_parse.parser.file_parser.pdf.pdf_parser import PdfParser


class TestPdfParser:
    def test_parse(self):
        class_under_test = PdfParser(LlmApiEnvSettings().to_settings())
        sample = RESOURCE_PATH / "sample_1.pdf"
        config = DocumentParserConfig()

        result = class_under_test.parse(sample, config)

        assert result is not None
