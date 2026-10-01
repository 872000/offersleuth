"""Salary parsing and sanity-checking against built-in market ranges."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import SalaryCheck

_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_RANGES = _PACKAGE_DIR.parent / "demo_data" / "salary_ranges.json"


def load_ranges(path: str | Path | None = None) -> dict:
    """Load the salary-range table (JSON). Pass your own file to customize."""
    with open(path or _DEFAULT_RANGES, encoding="utf-8") as fh:
        return json.load(fh)


# Matches: $65,000 / $65k / 65000 / $25/hr / $30 per hour / USD 70,000
_AMOUNT = r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(k)?"
_RANGE_SEP = r"\s*(?:-|–|—|to)\s*"
_PER_HOUR = re.compile(r"(?:/ ?hr|per hour|hourly|\bhr\b)", re.IGNORECASE)
_PER_MONTH = re.compile(r"(?:/ ?mo|per month|a month|monthly)", re.IGNORECASE)

_RANGE_RE = re.compile(
    rf"(?P<cur>USD|CAD|US\$|C\$|\$)?{_AMOUNT}{_RANGE_SEP}(?P<cur2>USD|CAD|US\$|C\$|\$)?{_AMOUNT}",
    re.IGNORECASE,
)
_SINGLE_RE = re.compile(rf"(?P<cur>USD|CAD|US\$|C\$|\$)\s*{_AMOUNT}", re.IGNORECASE)

_CA_HINTS = re.compile(
    r"\b(toronto|ontario|vancouver|montreal|calgary|ottawa|hamilton|canada|canadian|CAD|C\$)\b",
    re.IGNORECASE,
)
_US_HINTS = re.compile(
    r"\b(new york|san francisco|seattle|austin|boston|chicago|los angeles|united states|USD|US\$)\b",
    re.IGNORECASE,
)


def _to_number(raw: str, k_suffix: str | None) -> float:
    value = float(raw.replace(",", ""))
    if k_suffix:
        value *= 1000
    return value


def parse_salary(text: str) -> SalaryCheck:
    """Extract a salary figure from JD text, if present."""
    hourly = bool(_PER_HOUR.search(text))
    monthly = not hourly and bool(_PER_MONTH.search(text))

    def annualize(value: float) -> float:
        if hourly:
            return value * 2080
        if monthly:
            return value * 12
        return value

    match = _RANGE_RE.search(text)
    if match:
        low = annualize(_to_number(match.group(2), match.group(3)))
        high = annualize(_to_number(match.group(5), match.group(6)))
        currency = _detect_currency(match.group("cur") or match.group("cur2") or "", text)
        return SalaryCheck(True, low, high, currency, "year")

    match = _SINGLE_RE.search(text)
    if match:
        value = annualize(_to_number(match.group(2), match.group(3)))
        currency = _detect_currency(match.group("cur") or "", text)
        return SalaryCheck(True, value, value, currency, "year")

    return SalaryCheck(mentioned=False)


def _detect_currency(marker: str, text: str) -> str:
    marker = marker.upper()
    if "USD" in marker or "US$" in marker.replace(" ", ""):
        return "USD"
    if "CAD" in marker or marker.strip() == "C$":
        return "CAD"
    if _US_HINTS.search(text) and not _CA_HINTS.search(text):
        return "USD"
    return "CAD"  # default: Canadian job seeker context


def salary_sanity_check(
    salary: SalaryCheck,
    level: str = "entry",
    country: str | None = None,
    text_hint: str = "",
    ranges: dict | None = None,
) -> SalaryCheck:
    """Compare a parsed salary against market ranges; sets verdict + detail.

    Verdicts: healthy | low | high | vague | unknown.
    """
    if not salary.mentioned:
        salary.verdict = "vague"
        salary.detail = "No pay figure found in the posting."
        return salary

    table = ranges or load_ranges()
    country = (country or _detect_country(text_hint)).upper()
    band = table["ranges"].get(country, table["ranges"]["CA"]).get(level, table["ranges"]["CA"]["entry"])
    lo, hi = band["min"], band["max"]

    # Convert USD<->CAD crudely for comparison using the table's fx hint.
    fx = table.get("meta", {}).get("usd_to_cad", 1.36)
    low = salary.low * (fx if salary.currency == "USD" and country == "CA" else 1)
    high = salary.high * (fx if salary.currency == "USD" and country == "CA" else 1)

    if high < lo * 0.85:
        salary.verdict = "low"
        salary.detail = (
            f"Top of range ({_fmt(high)}) is well below the typical {level}-level "
            f"band ({_fmt(lo)}–{_fmt(hi)} {country}). Underpaid for the level."
        )
    elif low > hi * 1.25:
        salary.verdict = "high"
        salary.detail = (
            f"Bottom of range ({_fmt(low)}) is far above the typical {level}-level "
            f"band ({_fmt(lo)}–{_fmt(hi)} {country}). Unusually generous — or the "
            "level/scope is understated."
        )
    else:
        salary.verdict = "healthy"
        salary.detail = (
            f"Fits the typical {level}-level band ({_fmt(lo)}–{_fmt(hi)} {country})."
        )
    return salary


def _detect_country(text: str) -> str:
    if _US_HINTS.search(text) and not _CA_HINTS.search(text):
        return "US"
    return "CA"


def _fmt(value: float) -> str:
    return f"${value:,.0f}"
