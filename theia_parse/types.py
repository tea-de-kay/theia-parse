from typing import Literal


type ImageFormat = Literal["webp", "png", "jpeg"]
type RawParserTypeName = Literal["default", "llm"]
type ImageExtractionMethod = Literal["pymupdf", "yodocus"]

type BBox = tuple[float, float, float, float]
"""bbox = x0, top, x1, bottom"""
