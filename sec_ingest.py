"""SEC ingestion utilities for ticker lookup and company facts."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

SEC_HEADERS = {
    "User-Agent": "AI-Assisted Valuation (educational; contact: support@example.com)",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json",
}

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

TICKER_CIK_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


@dataclass
class CompanyProfile:
    cik: str
    ticker: str
    title: str


class SecRateLimiter:
    def __init__(self, min_interval: float = 0.2) -> None:
        self.min_interval = min_interval
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.time()


rate_limiter = SecRateLimiter()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _get_json(url: str) -> dict:
    rate_limiter.wait()
    response = requests.get(url, headers=SEC_HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def _cache_path(name: str) -> Path:
    return CACHE_DIR / name


def load_ticker_cik_mapping(force_refresh: bool = False) -> pd.DataFrame:
    cache_path = _cache_path("ticker_cik.json")
    if cache_path.exists() and not force_refresh:
        data = json.loads(cache_path.read_text())
    else:
        data = _get_json(TICKER_CIK_URL)
        cache_path.write_text(json.dumps(data))
    records = []
    for _, entry in data.items():
        records.append(
            {
                "ticker": entry["ticker"].upper(),
                "cik": str(entry["cik_str"]).zfill(10),
                "title": entry["title"],
            }
        )
    df = pd.DataFrame(records).drop_duplicates("ticker")
    return df


def build_ticker_index(df: pd.DataFrame) -> Dict[str, CompanyProfile]:
    index: Dict[str, CompanyProfile] = {}
    for _, row in df.iterrows():
        index[row["ticker"]] = CompanyProfile(
            cik=row["cik"], ticker=row["ticker"], title=row["title"]
        )
    return index


def search_tickers(index: Dict[str, CompanyProfile], query: str, limit: int = 20) -> List[CompanyProfile]:
    query = query.upper()
    matches = [profile for ticker, profile in index.items() if query in ticker]
    return matches[:limit]


def fetch_company_facts(cik: str) -> dict:
    cache_path = _cache_path(f"companyfacts_{cik}.json")
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    data = _get_json(COMPANY_FACTS_URL.format(cik=cik))
    cache_path.write_text(json.dumps(data))
    return data


def get_company_facts_by_ticker(ticker: str) -> Tuple[CompanyProfile, dict]:
    mapping = load_ticker_cik_mapping()
    index = build_ticker_index(mapping)
    ticker = ticker.upper()
    if ticker not in index:
        raise ValueError(f"Ticker {ticker} not found in SEC mapping.")
    profile = index[ticker]
    facts = fetch_company_facts(profile.cik)
    return profile, facts


def flatten_company_facts(facts: dict) -> pd.DataFrame:
    records: List[dict] = []
    facts_data = facts.get("facts", {})
    for taxonomy, tags in facts_data.items():
        for tag, detail in tags.items():
            units = detail.get("units", {})
            for unit, items in units.items():
                for item in items:
                    records.append(
                        {
                            "taxonomy": taxonomy,
                            "tag": tag,
                            "unit": unit,
                            "value": item.get("val"),
                            "fy": item.get("fy"),
                            "fp": item.get("fp"),
                            "form": item.get("form"),
                            "filed": item.get("filed"),
                            "end": item.get("end"),
                            "start": item.get("start"),
                            "accn": item.get("accn"),
                            "frame": item.get("frame"),
                        }
                    )
    df = pd.DataFrame(records)
    return df


def latest_fiscal_years(df: pd.DataFrame, years: int = 5) -> List[int]:
    years_available = sorted(df["fy"].dropna().unique())
    return years_available[-years:]


def select_facts_for_years(df: pd.DataFrame, years: Iterable[int]) -> pd.DataFrame:
    return df[df["fy"].isin(list(years))].copy()
