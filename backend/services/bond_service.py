"""Bond / Fixed Income Calculator — price, YTM, duration, cash flows."""
import math
from typing import Dict, List, Optional


def bond_price(face: float, coupon_rate: float, ytm: float, years: int, freq: int = 2) -> float:
    """Calculate bond price given YTM."""
    periods = years * freq
    c = face * coupon_rate / freq
    r = ytm / freq
    if r == 0:
        return c * periods + face
    pv_coupons = c * (1 - (1 + r) ** -periods) / r
    pv_face = face / (1 + r) ** periods
    return pv_coupons + pv_face


def bond_ytm(face: float, coupon_rate: float, price: float, years: int, freq: int = 2) -> float:
    """Solve for YTM via bisection."""
    lo, hi = 0.0001, 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        p = bond_price(face, coupon_rate, mid, years, freq)
        if abs(p - price) < 0.0001:
            return mid
        if p > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def macaulay_duration(face: float, coupon_rate: float, ytm: float, years: int, freq: int = 2) -> float:
    periods = years * freq
    c = face * coupon_rate / freq
    r = ytm / freq
    price = bond_price(face, coupon_rate, ytm, years, freq)
    weighted = sum(
        (t / freq) * c / (1 + r) ** t for t in range(1, periods)
    ) + (periods / freq) * (face + c) / (1 + r) ** periods
    return weighted / price


def cash_flow_schedule(face: float, coupon_rate: float, ytm: float, years: int, freq: int = 2) -> List[Dict]:
    periods = years * freq
    c = face * coupon_rate / freq
    r = ytm / freq
    rows = []
    for t in range(1, periods + 1):
        cf = c + (face if t == periods else 0)
        pv = cf / (1 + r) ** t
        rows.append({
            "period": t,
            "period_label": f"{'H' if freq == 2 else 'Q'}{t}" if freq != 1 else f"Y{t}",
            "year": round(t / freq, 2),
            "coupon": round(c, 2),
            "principal": face if t == periods else 0,
            "cash_flow": round(cf, 2),
            "pv": round(pv, 2),
        })
    return rows


def analyze_bond(
    face: float,
    coupon_rate: float,
    years: int,
    price: Optional[float] = None,
    ytm: Optional[float] = None,
    freq: int = 2,
    inflation: float = 2.5,
) -> Dict:
    if price is None and ytm is None:
        raise ValueError("Provide either price or YTM")

    if ytm is None:
        ytm = bond_ytm(face, coupon_rate, price, years, freq)
    if price is None:
        price = bond_price(face, coupon_rate, ytm, years, freq)

    mac_dur = macaulay_duration(face, coupon_rate, ytm, years, freq)
    mod_dur = mac_dur / (1 + ytm / freq)
    convexity_approx = mod_dur ** 2 + mod_dur  # simplified

    schedule = cash_flow_schedule(face, coupon_rate, ytm, years, freq)
    total_income = sum(r["coupon"] for r in schedule)

    # Price sensitivity: +/- 1% rate change
    price_up = bond_price(face, coupon_rate, ytm + 0.01, years, freq)
    price_down = bond_price(face, coupon_rate, ytm - 0.01, years, freq)

    real_yield = ytm - inflation / 100

    premium_discount = price - face
    status = "Premium" if premium_discount > 0 else "Discount" if premium_discount < 0 else "Par"

    return {
        "price": round(price, 4),
        "ytm_pct": round(ytm * 100, 4),
        "coupon_rate_pct": round(coupon_rate * 100, 2),
        "current_yield_pct": round(coupon_rate * face / price * 100, 4),
        "real_yield_pct": round(real_yield * 100, 4),
        "macaulay_duration": round(mac_dur, 4),
        "modified_duration": round(mod_dur, 4),
        "convexity": round(convexity_approx, 4),
        "total_coupon_income": round(total_income, 2),
        "price_if_rates_rise_1pct": round(price_up, 4),
        "price_if_rates_fall_1pct": round(price_down, 4),
        "pct_change_rates_rise": round((price_up - price) / price * 100, 4),
        "pct_change_rates_fall": round((price_down - price) / price * 100, 4),
        "premium_discount": round(premium_discount, 4),
        "status": status,
        "schedule": schedule,
    }
