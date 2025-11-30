from theia_parse.types import BBox


def clamp(bbox: BBox, width: float, height: float) -> BBox:
    x0, top, x1, bottom = bbox
    x0 = max(0, min(width, x0))
    top = max(0, min(height, top))
    x1 = max(0, min(width, x1))
    bottom = max(0, min(height, bottom))

    return x0, top, x1, bottom
