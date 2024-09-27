from theia_parse.llm.__spi__ import Prompt


MM_PDF_EXTRACT_CONTENT_SYSTEM_PROMPT = """
{% if system_prompt_preamble %}
{{ system_prompt_preamble }}
{% else %}
You are an expert for document parsing. You are precise, structured and always follow the given instructions.
{% endif %}

You are provided with:
{% if previous_parsed_pages %}
* the structured content of the previous page
{% endif %}
{% if previous_headings %}
* a list of previous headings in the document
{% endif %}
{% if raw_extracted %}
* a raw extracted text from a PDF page, which may be messy due to a complicated layout
{% endif %}
* an image of the full PDF page
{% if embedded_images %}
* enumerated embedded images from the full PDF page
{% endif %}

Your overall goal is to structure the full PDF page into a list of content blocks, indicating the type and content:
* type = 'heading-level-i': A heading of level i (= 1, 2, 3, ...), consistently formatted throughout the document. The content should include both the text of the heading and any associated numbering.
* type = 'text': A plain block of text, using Markdown formatting
* type = 'table': A table formatted as Markdown
* type = 'table-of-contents': A block containing an outline of the document, which may be spread across multiple pages
* type = 'footer': A block of text in the footer of the page
* type = 'image': A block containing a short description of an image which is relevant for the document (no logos or design elements)

Your task is to use the raw extracted text and image to identify the page layout and to extract the individual content blocks in the proper order from the page in a clean way.
Format your output as a JSON object, following this schema:
```
{'page_content': [{'type': 'one of: heading-level-i, text, table, table-of-contents, footer, image', 'content': 'the content as text', 'language': 'the language code'}, ...]}
```

# Instructions:

* Include all text from the raw extracted text and the image.
* Use the image to identify column layouts and extract each column of a column layout separately.
{% if custom_instructions %}
{% for instruction in custom_instructions %}
* {{ instruction }}
{% endfor %}
{% endif %}
"""  # noqa


MM_EXTRACT_CONTENT_USER_PROMPT = """
{% if previous_structured_page_content %}
# Previous structured page:
{'page_content': {{ previous_structured_page_content }}}
{% endif %}

{% if previous_headings %}
# Previous headings:
{{ previous_headings }}
{% endif %}

# Raw extracted pdf page text:
<raw_extracted_text>
{{ raw_extracted_text }}
</raw_extracted_text>

Think step by step and use the information above and the image to create the JSON object of the page content.
"""  # noqa

DEFAULT_PROMPTS = Prompts(
    mm_extract_content_system_prompt=Prompt(MM_PDF_EXTRACT_CONTENT_SYSTEM_PROMPT),
    mm_extract_content_user_prompt=Prompt(MM_EXTRACT_CONTENT_USER_PROMPT),
)
