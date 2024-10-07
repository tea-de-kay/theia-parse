from theia_parse.formatter.__spi__ import Formatter
from theia_parse.model import ContentElement, HeadingElement, ImageElement


class MarkdownFormatter(Formatter):
    def _format_heading(self, element: HeadingElement) -> str:
        return f"{'#'*element.heading_level} {element.content}"

    def _format_image(self, element: ImageElement) -> str:
        return f"![Image](/{element.medium_id})\n\nCaption: {element.content}"

    def _format_element(self, element: ContentElement) -> str:
        return element.content
