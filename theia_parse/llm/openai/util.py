import math

from theia_parse.model import LlmUsage


def calc_image_token_usage(
    width: int,
    height: int,
    base_tokens: int,
    tokens_per_tile: int,
    low_res: bool = False,
) -> LlmUsage:
    """
    Calculates token usage based on image dimensions, token counts and
    resolution detail.
    Based on https://platform.openai.com/docs/guides/vision/calculating-costs
    """

    if low_res or max(width, height) < 512:
        return LlmUsage(request_tokens=base_tokens)

    # Step 1: If either side exceeds 2048, scale down to fit within a 2048x2048 square
    if max(width, height) > 2048:
        scale_factor = 2048 / max(width, height)
        width = int(width * scale_factor)
        height = int(height * scale_factor)

    # Step 2: Scale the shortest side to 768px
    scale_factor = 768 / min(width, height)
    width = int(width * scale_factor)
    height = int(height * scale_factor)

    # Step 3: Calculate how many 512px tiles fit into the scaled image
    num_tiles_width = math.ceil(width / 512)
    num_tiles_height = math.ceil(height / 512)
    total_tiles = num_tiles_width * num_tiles_height

    # Step 4: Calculate the total token cost
    tokens = tokens_per_tile * total_tiles + base_tokens

    return LlmUsage(request_tokens=tokens)
