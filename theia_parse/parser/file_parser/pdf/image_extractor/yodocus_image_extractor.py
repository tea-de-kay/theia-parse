from pathlib import Path

from pdfplumber.page import Page
from yodocus import (
    DetectionConfig,
    Detector,
    HeuristicPostprocessor,
    PostprocessorConfig,
)

from theia_parse.parser.__spi__ import ImageExtractionConfig
from theia_parse.parser.file_parser.pdf.embedded_pdf_page_image import (
    EmbeddedPdfPageImage,
)
from theia_parse.parser.file_parser.pdf.image_extractor.__spi__ import ImageExtractor


class YodocusImageExtractor(ImageExtractor):
    def __init__(self, config: ImageExtractionConfig) -> None:
        super().__init__(config)
        self._detector = Detector(config.yodocus_model)
        self._yodocus_config = DetectionConfig(visualize=False)
        self._processor = HeuristicPostprocessor(config=PostprocessorConfig())

    def extract(self, path: Path, page: Page) -> list[EmbeddedPdfPageImage]:
        result = self._detector.detect(page.to_image().original, self._yodocus_config)
        result = self._processor.process(result, original_image=None)

        embedded_images: list[EmbeddedPdfPageImage] = []
        caption_idx = 1
        for box in result.boxes:
            x0 = box.x0 - 10
            top = box.y0 - 10
            x1 = box.x1 + 10
            bottom = box.y1 + 10
            raw_image = (
                page.crop((x0, top, x1, bottom), strict=False).to_image().original
            )
            img = EmbeddedPdfPageImage(
                page=page,
                raw_image=raw_image,
                caption_idx=caption_idx,
                config=self._config,
            )
            if img.is_relevant:
                embedded_images.append(img)
                caption_idx += 1

        embedded_images = sorted(embedded_images, key=lambda x: x.size, reverse=True)
        embedded_images = embedded_images[: self._config.max_images_per_page]

        for caption_idx, ei in enumerate(embedded_images, start=1):
            ei.caption_idx = caption_idx

        return embedded_images
