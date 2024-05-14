from theia_parse.llm.__spi__ import Prompt, Prompts


MM_EXTRACT_CONTENT_SYSTEM_PROMPT = """
{% if system_preamble %}
{{ system_preamble }}
{% else %}
You are an expert for document parsing for technical company documents.
{% endif %}

You are provided with:
* a raw extracted text from a pdf page, which may be messy due to a complicated layout and may be multilingual with a mix of languages
* an image of the pdf page
* the structured output of the previous page
* an optional list of previous headings in the document

Your overall goal is to get structured text from the pdf page, indicating headings, normal text, tables, ...

Your task is to use the raw extracted text and image, to extract the individual content blocks in the proper order from the page in a clean way and format your output as a JSON object following this schema:

```
{
    "page_content": [
        {"type": "one of: heading-level-i, text, table, footer", "content": "the text content", "language": "the language code"}
    ]
}
```
Make sure to:
* include all text
* identify headings and their level (1, 2, 3, ...) consistently
* use markdown formatting for tables and bullet points
* merge appropriate text blocks to yield a coherent reading experience
* strictly separate languages
* extract each column of a multilingual column layout separately
{% if custom_instructions %}
{% for instruction in custom_instructions %}
* {{ instruction }}
{% endfor %}
{% endif %}

"""  # noqa


MM_EXTRACT_CONTENT_USER_PROMPT = """
# Raw extracted pdf page text:
{{ raw_extracted_text }}

{% if previous_page %}
# Structured previous page:
{'page_content': {{ previous_page }} }
{% endif %}

{% if previous_headings %}
# Previous headings:
{{ previous_headings }}
{% endif %}

Use the information above and the image to create the JSON object of the page content.
"""

DEFAULT_PROMPTS = Prompts(
    mm_extract_content_system_prompt=Prompt(MM_EXTRACT_CONTENT_SYSTEM_PROMPT),
    mm_extract_content_user_prompt=Prompt(MM_EXTRACT_CONTENT_USER_PROMPT),
)
