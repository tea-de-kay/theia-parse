from tests.conftest import LOCAL_RESOURCE_PATH, RESOURCE_PATH
from theia_parse.llm.__spi__ import LlmApiEnvSettings
from theia_parse.parser.__spi__ import DocumentParserConfig, PromptConfig
from theia_parse.parser.file_parser.pdf.pdf_parser import PdfParser


class TestPdfParser:
    def test_parse(self):
        class_under_test = PdfParser(LlmApiEnvSettings().to_settings())
        sample = LOCAL_RESOURCE_PATH / "nvm_2018_043.pdf"
        config = DocumentParserConfig(
            post_improve=True,
            prompt_config=PromptConfig(
                custom_instructions=[
                    "The PDF page is in landscape format and represents 2 individual pages side by side. Parse first the left page and then the right page."  # noqa
                ]
            ),
        )

        result = class_under_test.parse(sample, config)

        assert result is not None
