"""Portfolio X-Ray — asset class, sector, and geographic breakdown using yfinance."""
import yfinance as yf
from typing import Dict, List
from collections import defaultdict


ASSET_CLASS_MAP = {
    "EQUITY": "Stocks", "ETF": "ETF", "MUTUALFUND": "Mutual Fund",
    "BOND": "Bonds", "FUTURE": "Futures", "OPTION": "Options",
    "CRYPTOCURRENCY": "Crypto", "CURRENCY": "Currency", "INDEX": "Index",
}

GEO_MAP = {
    "United States": "US", "China": "China", "Japan": "Japan",
    "United Kingdom": "UK", "Germany": "Germany", "France": "France",
    "Canada": "Canada", "India": "India", "South Korea": "South Korea",
    "Australia": "Australia", "Brazil": "Brazil", "Taiwan": "Taiwan",
}


def xray_portfolio(holdings: List[Dict]) -> Dict:
    """
    holdings: [{"ticker": "AAPL", "weight": 30.0}, ...]
    weights should sum to ~100 (%).
    """
    total_weight = sum(h["weight"] for h in holdings)
    if total_weight <= 0:
        raise ValueError("Total weight must be positive")

    sector_alloc: Dict[str, float] = defaultdict(float)
    asset_class_alloc: Dict[str, float] = defaultdict(float)
    geo_alloc: Dict[str, float] = defaultdict(float)
    holdings_detail = []

    for h in holdings:
        ticker = h["ticker"].upper().strip()
        weight = h["weight"] / total_weight * 100

        try:
            info = yf.Ticker(ticker).info
            quote_type = info.get("quoteType", "EQUITY")
            asset_cls = ASSET_CLASS_MAP.get(quote_type, quote_type)
            sector = info.get("sector") or info.get("category") or "Other"
            country = info.get("country", "Unknown")
            geo = GEO_MAP.get(country, country) if country else "Unknown"
            name = info.get("longName") or info.get("shortName", ticker)
            pe = info.get("trailingPE")
            div_yield = info.get("dividendYield")
            beta = info.get("beta")
            market_cap = info.get("marketCap")
        except Exception:
            asset_cls = "Unknown"
            sector = "Unknown"
            geo = "Unknown"
            name = ticker
            pe, div_yield, beta, market_cap = None, None, None, None

        sector_alloc[sector] += weight
        asset_class_alloc[asset_cls] += weight
        geo_alloc[geo] += weight

        holdings_detail.append({
            "ticker": ticker,
            "name": name,
            "weight": round(weight, 2),
            "asset_class": asset_cls,
            "sector": sector,
            "geography": geo,
            "pe_ratio": round(pe, 2) if pe else None,
            "dividend_yield_pct": round(div_yield * 100, 2) if div_yield else None,
            "beta": round(beta, 2) if beta else None,
            "market_cap": market_cap,
        })

    def sort_dict(d):
        return [{"label": k, "pct": round(v, 2)} for k, v in sorted(d.items(), key=lambda x: -x[1])]

    return {
        "holdings": holdings_detail,
        "sector_allocation": sort_dict(sector_alloc),
        "asset_class_allocation": sort_dict(asset_class_alloc),
        "geographic_allocation": sort_dict(geo_alloc),
        "total_tickers": len(holdings),
    }
