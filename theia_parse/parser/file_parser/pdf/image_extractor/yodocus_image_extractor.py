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
from theia_parse.types import BBox
from theia_parse.util.bbox import clamp


class YodocusImageExtractor(ImageExtractor):
    def __init__(self, config: ImageExtractionConfig) -> None:
        super().__init__(config)
        self._detector = Detector(config.yodocus_model)
        self._yodocus_config = DetectionConfig(
            confidence_threshold=config.yodocus_confidence_threshold,
            iou_threshold=config.yodocus_iou_threshold,
            visualize=False,
        )
        self._processor = HeuristicPostprocessor(
            config=PostprocessorConfig(
                containment_threshold=config.yodocus_postprocessor_containment_threshold
            )
        )

    def extract(self, path: Path, page: Page) -> list[EmbeddedPdfPageImage]:
        page_width, page_height = page.width, page.height
        if page_height < page_width and page_height < self._detector.input_height:
            input_image = page.to_image(height=self._detector.input_height)
            scale = self._detector.input_height / page_height
        elif page_width < self._detector.input_width:
            input_image = page.to_image(width=self._detector.input_width)
            scale = self._detector.input_width / page_width
        else:
            input_image = page.to_image()
            scale = 1

        result = self._detector.detect(input_image.original, self._yodocus_config)
        result = self._processor.process(result, original_image=None)

        embedded_images: list[EmbeddedPdfPageImage] = []
        embedded_images_bboxes: set[BBox] = set()
        caption_idx = 1
        for box in result.boxes:
            x0 = box.x0 / scale - self._config.yodocus_additional_margin
            top = box.y0 / scale - self._config.yodocus_additional_margin
            x1 = box.x1 / scale + self._config.yodocus_additional_margin
            bottom = box.y1 / scale + self._config.yodocus_additional_margin
            bbox = clamp((x0, top, x1, bottom), width=page_width, height=page_height)

            if bbox in embedded_images_bboxes:
                continue

            raw_image = (
                page.crop(bbox, relative=True, strict=False)
                .to_image(self._config.resolution)
                .original
            )
            img = EmbeddedPdfPageImage(
                page=page,
                raw_image=raw_image,
                caption_idx=caption_idx,
                config=self._config,
            )
            if img.is_relevant(self._config.resolution):
                embedded_images.append(img)
                caption_idx += 1
                embedded_images_bboxes.add(bbox)

        embedded_images = sorted(embedded_images, key=lambda x: x.size, reverse=True)
        embedded_images = embedded_images[: self._config.max_images_per_page]

        for caption_idx, ei in enumerate(embedded_images, start=1):
            ei.caption_idx = caption_idx

        return embedded_images
