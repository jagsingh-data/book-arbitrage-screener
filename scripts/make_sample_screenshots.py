"""Generate fake marketplace listing screenshots for the demo.

Real screenshots stay private (they show sellers' names and photos), so the
repo ships these synthetic ones instead. Run from the repo root:

    python scripts/make_sample_screenshots.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("sample_screenshots")

LISTINGS = [
    ("listing_01_nursing_lot.png", False, "$30", "Nursing school textbook bundle (3 books)",
     ["Like new, barely used. Pickup in Cypress.",
      "ISBN 978-3-98-259791-1",
      "ISBN 978-90-7483-378-3",
      "ISBN 9788762328600"]),
    ("listing_02_single.png", False, "$15", "Intro to Pharmacology textbook",
     ["Some highlighting in chapter 2.", "ISBN-13: 978-1-29-040479-2"]),
    ("listing_03_dark_mode.png", True, "$8", "Statistics textbook, 4th edition",
     ["Good condition, no writing inside.", "ISBN-10: 0-13-610804-0"]),
    ("listing_04_no_isbn.png", False, "$5", "Box of assorted paperbacks",
     ["Mixed fiction, about 20 books.", "Must go this week."]),
    ("listing_05_bad_check_digit.png", False, "$12", "Two anatomy books",
     ["ISBN 978-1-29-040479-3", "ISBN 978-6-66-972510-2"]),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for folder in ("/usr/share/fonts/truetype/dejavu/", ""):
        try:
            return ImageFont.truetype(folder + name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_listing(name, dark, price, title, lines):
    bg, fg, muted, photo = ((24, 25, 26), (228, 230, 235), (176, 179, 184), (58, 59, 60)) if dark \
        else ((255, 255, 255), (5, 5, 5), (101, 103, 107), (220, 223, 228))
    img = Image.new("RGB", (750, 1100), bg)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 750, 480), fill=photo)
    d.text((375, 240), "[ photo ]", font=font(28), fill=muted, anchor="mm")
    d.text((32, 510), title, font=font(30, True), fill=fg)
    d.text((32, 560), price, font=font(34, True), fill=fg)
    d.text((32, 615), "Listed 2 days ago in Houston, TX", font=font(22), fill=muted)
    d.text((32, 680), "Details", font=font(26, True), fill=fg)
    y = 730
    for line in lines:
        d.text((32, y), line, font=font(24), fill=fg)
        y += 44
    img.save(OUT / name)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for listing in LISTINGS:
        draw_listing(*listing)
    print(f"Wrote {len(LISTINGS)} screenshots to {OUT}/")
