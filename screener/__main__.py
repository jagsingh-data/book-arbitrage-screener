"""Command line entry point.

    python -m screener screenshots/ --offers data/sample_offers.csv
    python -m screener screenshots/            # live BookScouter offers (needs .env)
"""

import argparse
from pathlib import Path

import pandas as pd

from .offers import BookScouterOffers, CsvOffers
from .ocr import read_listing
from .profit import evaluate

IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank book listings by buyback profit.")
    parser.add_argument("images", type=Path, help="folder of listing screenshots")
    parser.add_argument("--offers", type=Path, help="CSV of offers (isbn13,vendor,price); omit to use the BookScouter API")
    parser.add_argument("--min-margin", type=float, default=0.5, help="minimum margin to buy, default 0.5 (50%%)")
    parser.add_argument("--fee-per-book", type=float, default=0.0, help="cost subtracted from each offer")
    parser.add_argument("--out", type=Path, default=Path("output"), help="folder for result CSVs")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    try:
        offers = CsvOffers(args.offers) if args.offers else BookScouterOffers()
    except RuntimeError as err:
        raise SystemExit(str(err))

    images = sorted(p for p in args.images.iterdir() if p.suffix.lower() in IMAGE_TYPES)
    if not images:
        raise SystemExit(f"No screenshots found in {args.images}")

    listings = []
    for path in images:
        listing = read_listing(path)
        note = "" if listing.isbns else "  (no valid ISBN found)"
        print(f"Read {path.name}: {len(listing.isbns)} ISBN(s), asking {listing.asking_price}{note}")
        listings.append(listing)

    ranked, books = evaluate(listings, offers, args.min_margin, args.fee_per_book)

    args.out.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(args.out / "ranked_listings.csv", index=False)
    books.to_csv(args.out / "book_offers.csv", index=False)

    with pd.option_context("display.width", 140, "display.max_columns", None):
        print("\nRanked listings:")
        print(ranked.to_string(index=False))
    print(f"\n{int(ranked['buy'].sum())} of {len(ranked)} listings clear the {args.min_margin:.0%} margin.")
    print(f"Saved results to {args.out}/")


if __name__ == "__main__":
    main()
