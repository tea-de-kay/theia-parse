from abc import ABC, abstractmethod
from collections.abc import Iterable

from theia_parse.model import ContentElement, HeadingElement, ImageElement


class Formatter(ABC):
    def format(self, content: Iterable[ContentElement], sep: str = "\n\n") -> str:
        return sep.join(self.format_element(e) for e in content)

    def format_element(self, element: ContentElement) -> str:
        if isinstance(element, HeadingElement):
            return self._format_heading(element)
        if isinstance(element, ImageElement):
            return self._format_image(element)

        return self._format_element(element)

    @abstractmethod
    def _format_image(self, element: ImageElement) -> str:
        pass

    @abstractmethod
    def _format_heading(self, element: HeadingElement) -> str:
        pass

    @abstractmethod
    def _format_element(self, element: ContentElement) -> str:
        pass
