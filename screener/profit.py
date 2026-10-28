"""Turn listings + offers into a ranked buy list.

A listing can hold one book or a whole lot, so profit is judged per listing:

    best_total = sum of the highest buyback offer for each book
    net_profit = best_total - asking_price
    margin     = net_profit / asking_price

A listing passes when margin >= min_margin (0.50 by default). Buyback
vendors usually pay shipping, so no shipping cost is subtracted; pass
--fee-per-book to model one if a vendor charges it.
"""

import pandas as pd

from .ocr import Listing


def evaluate(listings: list[Listing], offers, min_margin: float = 0.5, fee_per_book: float = 0.0):
    book_rows, listing_rows = [], []

    for listing in listings:
        best_total, priced = 0.0, 0
        for isbn in listing.isbns:
            vendor_offers = offers.get_offers(isbn)
            best = max(vendor_offers, key=lambda o: o.price, default=None)
            if best:
                priced += 1
                best_total += best.price - fee_per_book
            book_rows.append({
                "listing": listing.source,
                "isbn13": isbn,
                "best_vendor": best.vendor if best else None,
                "best_offer": best.price if best else 0.0,
                "vendors_quoting": len(vendor_offers),
            })

        asking = listing.asking_price
        # No ISBNs or no price means there is nothing to judge, not a loss.
        judgeable = asking is not None and priced > 0
        profit = best_total - asking if judgeable else None
        margin = profit / asking if profit is not None and asking else None
        listing_rows.append({
            "listing": listing.source,
            "books_found": len(listing.isbns),
            "books_with_offers": priced,
            "asking_price": asking,
            "best_buyback_total": round(best_total, 2),
            "net_profit": round(profit, 2) if profit is not None else None,
            "margin": round(margin, 3) if margin is not None else None,
            "buy": bool(margin is not None and margin >= min_margin),
        })

    listings_df = pd.DataFrame(listing_rows)
    if not listings_df.empty:
        listings_df = listings_df.sort_values(
            ["buy", "net_profit"], ascending=[False, False], na_position="last"
        ).reset_index(drop=True)
    return listings_df, pd.DataFrame(book_rows)
