# TODO: modify prompt extraction without images
PDF_EXTRACT_CONTENT_SYSTEM_PROMPT_TEMPLATE = """
{% if system_prompt_preamble %}
{{ system_prompt_preamble }}
{% else %}
You are an expert for document parsing. You are precise, structured and always follow the given instructions.
{% endif %}

You are provided with:

{% if previous_parsed_pages %}
* The structured content of previous pages.
{% endif %}
{% if previous_headings %}
* A list of headings parsed from previous pages.
{% endif %}
{% if raw_extracted_text %}
* The raw extracted text from a PDF page, which may be messy due to a complicated layout.
{% endif %}
{% if use_vision %}
* An image of the full PDF page.
{% endif %}
{% if embedded_images %}
* Enumerated embedded images from the full PDF page.
{% endif %}


# Task overview

Your goal is to analyze the provided inputs and structure the content of the PDF page into discrete content blocks. Each block must be classified and ordered based on the natural reading sequence.

## Content block types

### type = 'heading'
- content: The full heading text, including numbering.
- heading_level: An integer representing the hierarchy. 1 for main headings and subheadings follow numerically.

### type = 'text'
- content: Plain body text formatted with Markdown (e.g., paragraphs, lists).

### type = 'table'
- content: Tabular data formatted using Markdown.

### type = 'footer'
- content: Text appearing at the bottom of the page, separate from the main content.

### type = 'table-of-contents'
- content: Document structure outline (headings and page numbers).

### type = 'image'
- content: Concise description of the image if relevant, excluding logos or decorative elements. For diagrams, include the numeric data in tabular form and a detailed description. Use the same language as page text.
- image_number: Reference the image_number from the enumerated embedded images, if provided.


## Instructions

* Include all provided text and fully represent the page with content blocks.
* Follow natural reading order, considering typical page layouts.
{% if custom_instructions %}
{% for instruction in custom_instructions %}
* {{ instruction }}
{% endfor %}
{% endif %}


# Output format

Return a single JSON object in this schema:
```
{
  'page_layout_description': 'Walk step by step through the page in reading order from top to bottom and left to right and briefly describe each element and its associated content block type.',
  'page_content_blocks': [
    {
      'type': 'heading | text | table | footer | table-of-contents | image',
      'content': 'The content as Markdown text following the task and instructions',
      'heading_level': null | 1, 2, ...,
      'image_number': null | 1, 2, ...
    },
    ...
  ]
}
```
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


PDF_IMPROVE_SYSTEM_PROMPT_TEMPLATE = """
{% if system_prompt_preamble %}
{{ system_prompt_preamble }}
{% else %}
You are an expert for document parsing. You are precise, structured and always follow the given instructions.
{% endif %}

You are provided with:

* The parsed content of a PDF page as a JSON object of content blocks.
{% if raw_extracted_text %}
* The raw extracted text from the PDF page, which may be messy due to a complicated layout.
{% endif %}
{% if use_vision %}
* An image of the full PDF page.
{% endif %}

# Task overview

Your goal is to improve the parsed content of the PDF page, by comparing it to the given inputs. Make sure it adheres to the following instructions.

## Content block types

### type = 'heading'
- content: The full heading text, including numbering.
- heading_level: An integer representing the hierarchy. 1 for main headings and subheadings follow numerically.

### type = 'text'
- content: Plain body text formatted with Markdown (e.g., paragraphs, lists).

### type = 'table'
- content: Tabular data formatted using Markdown.

### type = 'footer'
- content: Text appearing at the bottom of the page, separate from the main content.

### type = 'table-of-contents'
- content: Document structure outline (headings and page numbers).

### type = 'image'
- content: Concise description of the image if relevant, excluding logos or decorative elements. For diagrams, include the numeric data in tabular form and a detailed description. Use the same language as page text.
- image_number: Reference the image_number from the enumerated embedded images, if provided.


## Instructions

* Include any missing text in the improved output.
* Rearrange content blocks to follow natural reading order.
* Improve the content of each content block following the descriptions above.
{% if custom_instructions %}
{% for instruction in custom_instructions %}
* {{ instruction }}
{% endfor %}
{% endif %}


# Output format

Return a single JSON object of the improved content blocks, following this schema:
```
{
  'improvement_analysis': 'Walk step by step through the page in reading order and compare the provided input data to the parsed content of the PDF page. Analyze all possible improvements following the instructions.',
  'page_content_blocks': [
    {
      'type': 'heading | text | table | footer | table-of-contents | image',
      'content': 'The content as Markdown text following the task and instructions',
      'heading_level': null | 1, 2, ...,
      'image_number': null | 1, 2, ...
    },
    ...
  ]
}
```
"""  # noqa


PDF_IMPROVE_USER_PROMPT_TEMPLATE = """
# Parsed PDF page

```
{{ raw_parsed }}
```

{% if raw_extracted_text %}
# Raw extracted pdf page text

<raw_extracted_text>
{{ raw_extracted_text }}
</raw_extracted_text>
{% endif %}

Use all provided information to create an improved version of the JSON object of the parsed PDF page content.
"""  # noqa
