from screener.isbn import extract_isbns, is_valid_isbn10, is_valid_isbn13, normalize, to_isbn13
from screener.ocr import parse_price


def test_valid_isbn13():
    assert is_valid_isbn13("9780136108047")
    assert not is_valid_isbn13("9780136108048")  # wrong check digit


def test_valid_isbn10_including_x():
    assert is_valid_isbn10("0136108040")
    assert is_valid_isbn10("080442957X")
    assert not is_valid_isbn10("0136108041")


def test_isbn10_converts_to_isbn13():
    assert to_isbn13("0136108040") == "9780136108047"
    assert normalize("0-13-610804-0") == "9780136108047"


def test_fixes_common_ocr_misreads():
    # Tesseract often reads 0 as O and 1 as l.
    assert normalize("978O136lO8047") == "9780136108047"


def test_extract_skips_bad_check_digits_and_dedupes():
    text = "ISBN 978-0-13-610804-7, again 9780136108047, typo 978-0-13-610804-8"
    assert extract_isbns(text) == ["9780136108047"]


def test_extract_ignores_phone_numbers():
    assert extract_isbns("Call 832-555-0199 or text 2815550123") == []


def test_parse_price():
    assert parse_price("Nursing bundle\n$1,250\nListed today") == 1250.0
    assert parse_price("$ 8.50 firm") == 8.5
    assert parse_price("free to a good home") is None
