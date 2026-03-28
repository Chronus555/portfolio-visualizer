"""
Tax-Loss Harvesting Scanner Service
Identifies positions with unrealized losses and estimates tax savings.
"""
import logging
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# IRS wash-sale window: 30 days before AND after sale
WASH_SALE_DAYS = 30


def scan_tax_harvest(
    positions: List[Dict],      # [{ticker, shares, cost_basis, purchase_date}, ...]
    tax_rate_st: float = 0.37,  # short-term (ordinary income) rate
    tax_rate_lt: float = 0.20,  # long-term capital gains rate
    state_tax_rate: float = 0.0,
) -> Dict:
    """
    Scan a portfolio for tax-loss harvesting opportunities.
    Returns candidates sorted by potential tax savings.
    """
    today = datetime.now().date()
    results = []
    total_harvestable_loss = 0.0
    total_tax_savings = 0.0
    total_positions = len(positions)

    # Fetch current prices in batch
    tickers = [p["ticker"] for p in positions]
    price_map = _fetch_current_prices(tickers)

    for pos in positions:
        ticker   = pos["ticker"]
        shares   = float(pos.get("shares", 0))
        basis    = float(pos.get("cost_basis", 0))   # per share
        purchase_date_str = pos.get("purchase_date", "")
        name     = pos.get("name", ticker)

        current_price = price_map.get(ticker)
        if current_price is None or shares <= 0 or basis <= 0:
            continue

        total_cost     = basis * shares
        current_value  = current_price * shares
        unrealized_pnl = current_value - total_cost
        unrealized_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0

        # Determine holding period
        is_long_term = False
        holding_days = None
        if purchase_date_str:
            try:
                purchase_date = datetime.strptime(purchase_date_str[:10], "%Y-%m-%d").date()
                holding_days  = (today - purchase_date).days
                is_long_term  = holding_days > 365
            except Exception:
                pass

        # Only flag positions with losses
        if unrealized_pnl >= 0:
            results.append({
                "ticker":         ticker,
                "name":           name,
                "shares":         shares,
                "cost_basis":     round(basis, 4),
                "current_price":  round(current_price, 4),
                "current_value":  round(current_value, 2),
                "total_cost":     round(total_cost, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pct": round(unrealized_pct, 2),
                "holding_days":   holding_days,
                "is_long_term":   is_long_term,
                "is_candidate":   False,
                "tax_savings":    0,
                "tax_rate_used":  0,
                "wash_sale_risk": False,
                "similar_etfs":   [],
                "harvest_note":   "No unrealized loss",
            })
            continue

        # Calculate tax savings
        effective_rate = (tax_rate_lt + state_tax_rate) if is_long_term else (tax_rate_st + state_tax_rate)
        tax_savings    = abs(unrealized_pnl) * effective_rate
        total_harvestable_loss += abs(unrealized_pnl)
        total_tax_savings      += tax_savings

        # Suggest replacement ETFs (to maintain exposure while avoiding wash sale)
        similar = _get_similar_etfs(ticker)

        results.append({
            "ticker":         ticker,
            "name":           name,
            "shares":         shares,
            "cost_basis":     round(basis, 4),
            "current_price":  round(current_price, 4),
            "current_value":  round(current_value, 2),
            "total_cost":     round(total_cost, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pct": round(unrealized_pct, 2),
            "holding_days":   holding_days,
            "is_long_term":   is_long_term,
            "is_candidate":   True,
            "tax_savings":    round(tax_savings, 2),
            "tax_rate_used":  round(effective_rate * 100, 2),
            "wash_sale_risk": False,  # UI will show warning to check manually
            "similar_etfs":   similar,
            "harvest_note":   _make_note(unrealized_pnl, holding_days, is_long_term),
        })

    # Sort by tax savings descending
    candidates = [r for r in results if r["is_candidate"]]
    non_candidates = [r for r in results if not r["is_candidate"]]
    candidates.sort(key=lambda x: x["tax_savings"], reverse=True)

    return {
        "summary": {
            "total_positions":          total_positions,
            "candidates_count":         len(candidates),
            "total_harvestable_loss":   round(total_harvestable_loss, 2),
            "estimated_tax_savings":    round(total_tax_savings, 2),
            "tax_rate_st":              round(tax_rate_st * 100, 2),
            "tax_rate_lt":              round(tax_rate_lt * 100, 2),
            "state_tax_rate":           round(state_tax_rate * 100, 2),
        },
        "candidates": candidates,
        "all_positions": candidates + non_candidates,
        "disclaimer": (
            "This analysis is for educational purposes only and does not constitute tax advice. "
            "Consult a qualified tax professional before making tax-motivated investment decisions. "
            "Wash-sale rules may apply — verify a 30-day window before and after any sale."
        ),
    }


def _fetch_current_prices(tickers: List[str]) -> Dict[str, float]:
    """Fetch latest closing prices for a list of tickers."""
    price_map = {}
    if not tickers:
        return price_map
    try:
        data = yf.download(tickers, period="5d", auto_adjust=True, progress=False)
        if hasattr(data.columns, "levels"):
            closes = data["Close"]
        else:
            closes = data[["Close"]]
            closes.columns = tickers
        latest = closes.iloc[-1]
        for t in tickers:
            if t in latest.index and not pd.isna(latest[t]):
                price_map[t] = float(latest[t])
    except Exception as e:
        logger.warning("Price fetch error: %s", e)
        # Fallback: fetch individually
        for t in tickers:
            try:
                hist = yf.Ticker(t).history(period="5d")
                if not hist.empty:
                    price_map[t] = float(hist["Close"].iloc[-1])
            except Exception:
                pass
    return price_map


import pandas as pd


def _get_similar_etfs(ticker: str) -> List[Dict]:
    """Return similar/replacement ETFs to avoid wash-sale while maintaining exposure."""
    SIMILAR_MAP = {
        # US Broad Market
        "SPY":  [{"ticker": "IVV",  "name": "iShares Core S&P 500"},
                 {"ticker": "VOO",  "name": "Vanguard S&P 500"}],
        "IVV":  [{"ticker": "SPY",  "name": "SPDR S&P 500"},
                 {"ticker": "VOO",  "name": "Vanguard S&P 500"}],
        "VOO":  [{"ticker": "SPY",  "name": "SPDR S&P 500"},
                 {"ticker": "IVV",  "name": "iShares Core S&P 500"}],
        "VTI":  [{"ticker": "ITOT", "name": "iShares Core S&P Total Mkt"},
                 {"ticker": "SCHB", "name": "Schwab US Broad Market"}],
        "ITOT": [{"ticker": "VTI",  "name": "Vanguard Total Stock Market"},
                 {"ticker": "SCHB", "name": "Schwab US Broad Market"}],
        # Growth
        "QQQ":  [{"ticker": "QQQM", "name": "Invesco NASDAQ 100"},
                 {"ticker": "VGT",  "name": "Vanguard Info Technology"}],
        "VGT":  [{"ticker": "XLK",  "name": "Technology Select SPDR"},
                 {"ticker": "QQQ",  "name": "Invesco QQQ"}],
        # International
        "VXUS": [{"ticker": "IXUS", "name": "iShares Core MSCI Total Intl"},
                 {"ticker": "VEA",  "name": "Vanguard FTSE Dev Markets"}],
        "VEA":  [{"ticker": "EFA",  "name": "iShares MSCI EAFE"},
                 {"ticker": "VXUS", "name": "Vanguard Total Intl Stock"}],
        "EFA":  [{"ticker": "VEA",  "name": "Vanguard FTSE Dev Markets"},
                 {"ticker": "SCHF", "name": "Schwab Intl Equity"}],
        # Bonds
        "AGG":  [{"ticker": "BND",  "name": "Vanguard Total Bond Market"},
                 {"ticker": "SCHZ", "name": "Schwab US Aggregate Bond"}],
        "BND":  [{"ticker": "AGG",  "name": "iShares Core US Aggregate Bond"},
                 {"ticker": "SCHZ", "name": "Schwab US Aggregate Bond"}],
        "TLT":  [{"ticker": "VGLT", "name": "Vanguard Long-Term Treasury"},
                 {"ticker": "IEF",  "name": "iShares 7-10 Year Treasury"}],
        # Small Cap
        "IWM":  [{"ticker": "VB",   "name": "Vanguard Small-Cap"},
                 {"ticker": "SCHA", "name": "Schwab US Small-Cap"}],
        "VB":   [{"ticker": "IWM",  "name": "iShares Russell 2000"},
                 {"ticker": "IJR",  "name": "iShares Core S&P Small-Cap"}],
        # Value
        "VTV":  [{"ticker": "IVE",  "name": "iShares S&P 500 Value"},
                 {"ticker": "SCHV", "name": "Schwab US Large-Cap Value"}],
        # REITs
        "VNQ":  [{"ticker": "IYR",  "name": "iShares US Real Estate"},
                 {"ticker": "SCHH", "name": "Schwab US REIT"}],
        # Gold
        "GLD":  [{"ticker": "IAU",  "name": "iShares Gold Trust"},
                 {"ticker": "GLDM", "name": "SPDR Gold MiniShares"}],
        "IAU":  [{"ticker": "GLD",  "name": "SPDR Gold Shares"},
                 {"ticker": "GLDM", "name": "SPDR Gold MiniShares"}],
    }
    return SIMILAR_MAP.get(ticker.upper(), [])


def _make_note(pnl: float, holding_days: Optional[int], is_long_term: bool) -> str:
    """Generate a plain-language harvest recommendation note."""
    loss = abs(pnl)
    term = "long-term" if is_long_term else "short-term"
    if holding_days and holding_days < 30:
        return f"Very recent purchase ({holding_days}d). Verify no wash-sale conflict with prior 30-day window."
    if loss < 100:
        return "Small loss — transaction costs may outweigh benefit."
    return f"${loss:,.0f} {term} loss available to harvest. Replace with similar ETF to maintain exposure."
