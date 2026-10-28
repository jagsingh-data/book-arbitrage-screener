"""ISBN cleaning, validation, and extraction from OCR text.

OCR output is noisy, so this module does three things:
1. Normalizes common OCR misreads (O -> 0, l/I -> 1, S -> 5, B -> 8).
2. Pulls ISBN-shaped candidates out of free text with a regex.
3. Keeps only candidates whose check digit is valid, which filters out
   misreads instead of sending bad ISBNs to the pricing step.
"""

import re

# Characters Tesseract commonly confuses with digits inside an ISBN.
_OCR_FIXES = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "|": "1", "S": "5", "B": "8"})

# 13 digits starting with 978/979, or 9 digits + a final digit or X,
# allowing spaces and hyphens between digits.
_CANDIDATE = re.compile(
    r"(?<![0-9])"
    r"(97[89](?:[\s-]?[0-9OolISB|]){10}"
    r"|[0-9OolISB|](?:[\s-]?[0-9OolISB|]){8}[\s-]?[0-9OolISB|Xx])"
    r"(?![0-9])"
)


def clean(raw: str) -> str:
    """Strip spaces and hyphens, fix OCR misreads, uppercase a trailing x."""
    digits = re.sub(r"[\s-]", "", raw).translate(_OCR_FIXES)
    return digits[:-1] + digits[-1].upper() if digits else digits


def is_valid_isbn10(isbn: str) -> bool:
    """ISBN-10: weights 10 down to 1, total divisible by 11. X means 10."""
    if not re.fullmatch(r"[0-9]{9}[0-9X]", isbn):
        return False
    total = sum((10 - i) * int(ch) for i, ch in enumerate(isbn[:9]))
    total += 10 if isbn[9] == "X" else int(isbn[9])
    return total % 11 == 0


def is_valid_isbn13(isbn: str) -> bool:
    """ISBN-13: weights alternate 1 and 3, total divisible by 10."""
    if not re.fullmatch(r"97[89][0-9]{10}", isbn):
        return False
    total = sum((1 if i % 2 == 0 else 3) * int(ch) for i, ch in enumerate(isbn))
    return total % 10 == 0


def to_isbn13(isbn10: str) -> str:
    """Convert a valid ISBN-10 to its ISBN-13 form (978 prefix + new check digit)."""
    core = "978" + isbn10[:9]
    total = sum((1 if i % 2 == 0 else 3) * int(ch) for i, ch in enumerate(core))
    return core + str((10 - total % 10) % 10)


def normalize(raw: str) -> str | None:
    """Return a valid ISBN-13 for any valid ISBN-10/13 input, else None."""
    isbn = clean(raw)
    if is_valid_isbn13(isbn):
        return isbn
    if is_valid_isbn10(isbn):
        return to_isbn13(isbn)
    return None


def extract_isbns(text: str) -> list[str]:
    """Find every valid ISBN in a block of text, returned as unique ISBN-13s in order."""
    found: list[str] = []
    for match in _CANDIDATE.finditer(text):
        isbn13 = normalize(match.group(0))
        if isbn13 and isbn13 not in found:
            found.append(isbn13)
    return found
