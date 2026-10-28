"""Where buyback offers come from.

Two sources share one interface, get_offers(isbn13) -> list of Offer:

- CsvOffers reads offers from a CSV file. It needs no API key, so anyone
  cloning the repo can run the project end to end with the sample data.
- BookScouterOffers calls the BookScouter API for live offers. It reads the
  key and endpoint from environment variables (see .env.example) and caches
  responses so the same ISBN is not requested twice.
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests


@dataclass(frozen=True)
class Offer:
    vendor: str
    price: float


class CsvOffers:
    """Offers from a CSV with columns: isbn13, vendor, price."""

    def __init__(self, path: Path):
        df = pd.read_csv(path, dtype={"isbn13": str})
        self._by_isbn = {
            isbn: [Offer(r.vendor, float(r.price)) for r in group.itertuples()]
            for isbn, group in df.groupby("isbn13")
        }

    def get_offers(self, isbn13: str) -> list[Offer]:
        return self._by_isbn.get(isbn13, [])


class BookScouterOffers:
    """Live buyback offers from the BookScouter API.

    BookScouter issues API keys through its data services program. Set
    BOOKSCOUTER_API_KEY and BOOKSCOUTER_API_URL in a .env file; the URL is
    the prices endpoint from the docs BookScouter gives you, with {isbn}
    where the ISBN goes. Check the response field names below against those
    docs, since they may differ by plan.
    """

    def __init__(self, cache_path: Path = Path(".cache/offers.json"), delay_s: float = 1.0):
        self.api_key = os.environ.get("BOOKSCOUTER_API_KEY")
        self.url = os.environ.get("BOOKSCOUTER_API_URL")
        if not self.api_key or not self.url:
            raise RuntimeError(
                "Set BOOKSCOUTER_API_KEY and BOOKSCOUTER_API_URL in .env, "
                "or run with --offers path/to/offers.csv instead."
            )
        self.delay_s = delay_s
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    def get_offers(self, isbn13: str) -> list[Offer]:
        if isbn13 not in self.cache:
            resp = requests.get(
                self.url.format(isbn=isbn13),
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=20,
            )
            resp.raise_for_status()
            self.cache[isbn13] = resp.json()
            self._save_cache()
            time.sleep(self.delay_s)  # stay polite with the rate limit
        return self._parse(self.cache[isbn13])

    @staticmethod
    def _parse(payload) -> list[Offer]:
        rows = payload.get("prices", payload.get("data", [])) if isinstance(payload, dict) else payload
        offers = []
        for row in rows or []:
            vendor = row.get("vendorName") or row.get("vendor") or str(row.get("vendorId", "unknown"))
            price = row.get("price")
            if price is not None and float(price) > 0:
                offers.append(Offer(vendor, float(price)))
        return offers

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2))
