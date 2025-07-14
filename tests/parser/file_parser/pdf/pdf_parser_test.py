from tests.conftest import LOCAL_RESOURCE_PATH, RESOURCE_PATH
from theia_parse.llm.__spi__ import LlmApiEnvSettings
from theia_parse.parser.__spi__ import (
    DocumentParserConfig,
    PromptConfig,
    RawParserConfig,
)
from theia_parse.parser.file_parser.pdf.pdf_parser import PdfParser


class TestPdfParser:
    def test_parse(self):
        class_under_test = PdfParser(LlmApiEnvSettings().to_settings())
        sample = LOCAL_RESOURCE_PATH / ""
        config = DocumentParserConfig(
            post_improve=False,
            prompt_config=PromptConfig(),
            raw_parser_config=RawParserConfig(),
        )

        result = class_under_test.parse(sample, config)

        assert result is not None
