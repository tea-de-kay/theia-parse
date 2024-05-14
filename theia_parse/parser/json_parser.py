import json
from typing import Any

from theia_parse.util.log import LogFactory


class JsonParser:
    _log = LogFactory.get_logger()

    def parse(self, text: str) -> dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}") + 1
        text = text[start:end]

        try:
            return json.loads(text)
        except Exception as e:
            self._log.error(
                "Could not parse JSON  [text='{0}', error='{1}']", text, str(e)
            )
            return {}
