"""Read ISBNs and the asking price from a listing screenshot.

Pipeline: load image -> grayscale -> upscale -> denoise -> threshold -> Tesseract.
Upscaling and thresholding matter most: phone screenshots have small text and
colored backgrounds, and Tesseract reads clean black-on-white text far better.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from .isbn import extract_isbns

_PRICE = re.compile(r"\$\s?([0-9]{1,4}(?:,[0-9]{3})*(?:\.[0-9]{2})?)")


@dataclass
class Listing:
    source: str
    isbns: list[str] = field(default_factory=list)
    asking_price: float | None = None
    raw_text: str = ""


def preprocess(image: np.ndarray) -> np.ndarray:
    """Turn a color screenshot into a clean, high-contrast black-and-white image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Dark-mode screenshots come out as white text on black; flip so text is dark.
    if np.mean(binary) < 127:
        binary = cv2.bitwise_not(binary)
    return binary


def read_text(image_path: Path) -> str:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not open image: {image_path}")
    processed = preprocess(image)
    # psm 6 treats the screenshot as one block of text, which suits listing pages.
    return pytesseract.image_to_string(processed, config="--oem 3 --psm 6")


def parse_price(text: str) -> float | None:
    """Return the first dollar amount in the text, which on a listing is the asking price."""
    match = _PRICE.search(text)
    return float(match.group(1).replace(",", "")) if match else None


def read_listing(image_path: Path) -> Listing:
    text = read_text(image_path)
    return Listing(
        source=image_path.name,
        isbns=extract_isbns(text),
        asking_price=parse_price(text),
        raw_text=text,
    )
