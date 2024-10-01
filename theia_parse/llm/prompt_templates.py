PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE = """
{% if system_prompt_preamble %}
{{ system_prompt_preamble }}
{% else %}
You are an expert for document parsing. You are precise, structured and always follow the given instructions.
{% endif %}

You are provided with:

{% if previous_parsed_pages %}
* the structured content of previous pages
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


# Your task

Your overall goal is to structure the full PDF page into a list of content blocks, indicating the type and content:

* type = 'heading-level-i': A heading of level i (= 1, 2, ... 10), consistently formatted throughout the document. The content should include both the text of the heading and any associated numbering.
* type = 'text': A plain block of text, using Markdown formatting
* type = 'table': A table formatted as Markdown
* type = 'footer': A block of text in the footer of the page
* type = 'table-of-contents': A block containing an outline of the document, which may be spread across multiple pages
{% if embedded_images %}
* type = 'image': A block containing an image which is relevant for the document (no logos or design elements). The content must start with "image_number=IMG_NR" where the image_number is provided by the corresponding enumerated embedded image (image_number = IMG_NR). Furthermore the content must contain a concise description of the image.
{% else %}
* type = 'image': A block containing an image which is relevant for the document (no logos or design elements). The content must contain a concise description of the image.
{% endif %}

Your task is to use everything provided to you to identify the page layout and content and extract the individual content blocks in proper reading order.

Output a single JSON object, following this schema:
```
{
  'page_content_blocks': [
    {
      'type': 'heading-level-i (i = 1, 2, ... 10) | text | table | footer | table-of-contents | image',
      'content': 'the content as text following the instructions'
    },
    ...
  ]
}
```

# Instructions

* Include all text provided to you.
* Make the content blocks as large and consistent as possible.
{% if custom_instructions %}
{% for instruction in custom_instructions %}
* {{ instruction }}
{% endfor %}
{% endif %}
"""  # noqa


PDF_EXTRACT_CONTENT_USER_PROMPT_TEMPLATE = """
{% if previous_parsed_pages %}
# Previous structured pages
{% for page in previous_parsed_pages %}
```
{
  'page_content_blocks': {{ page }}
}
```
{% endfor %}
{% endif %}

{% if previous_headings %}
# Previous headings
{% for heading in previous_headings %}
{{ heading }}
{% endfor %}
{% endif %}

{% if raw_extracted_text %}
# Raw extracted pdf page text
<raw_extracted_text>
{{ raw_extracted_text }}
</raw_extracted_text>
{% endif %}

Use all provided information to create the JSON object of the page content.
"""  # noqa
