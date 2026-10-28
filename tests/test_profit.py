import pandas as pd

from screener.offers import Offer
from screener.ocr import Listing
from screener.profit import evaluate


class FakeOffers:
    def __init__(self, table):
        self.table = table

    def get_offers(self, isbn13):
        return self.table.get(isbn13, [])


def test_lot_uses_best_offer_per_book_and_ranks_buys_first():
    offers = FakeOffers({
        "A": [Offer("v1", 10.0), Offer("v2", 14.0)],
        "B": [Offer("v1", 9.0)],
        "C": [Offer("v1", 11.0)],
    })
    listings = [
        Listing("lot.png", ["A", "B"], asking_price=10.0),   # 23 back on 10 -> 130% margin
        Listing("single.png", ["C"], asking_price=10.0),     # 11 back on 10 -> 10% margin
        Listing("empty.png", [], asking_price=5.0),          # nothing to judge
    ]
    ranked, books = evaluate(listings, offers, min_margin=0.5)

    assert list(ranked["listing"]) == ["lot.png", "single.png", "empty.png"]
    lot = ranked.iloc[0]
    assert lot["best_buyback_total"] == 23.0 and lot["net_profit"] == 13.0 and lot["buy"]
    assert not ranked.iloc[1]["buy"]
    assert pd.isna(ranked.iloc[2]["net_profit"])
    assert books.loc[books.isbn13 == "A", "best_vendor"].item() == "v2"
