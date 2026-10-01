"""Tests for salary parsing and sanity-checking."""

from offersleuth.salary import load_ranges, parse_salary, salary_sanity_check


def test_parse_range():
    s = parse_salary("Salary: $65,000 - $80,000 per year.")
    assert s.mentioned
    assert s.low == 65000
    assert s.high == 80000


def test_parse_k_suffix():
    s = parse_salary("Pay is $65k-$80k.")
    assert s.mentioned
    assert s.low == 65000
    assert s.high == 80000


def test_parse_hourly_normalized():
    s = parse_salary("Rate: $35/hr, Toronto.")
    assert s.mentioned
    assert s.low == 35 * 2080


def test_parse_monthly_normalized():
    s = parse_salary("Earn $5,000/month from home.")
    assert s.mentioned
    assert s.low == 5000 * 12


def test_parse_missing():
    s = parse_salary("Competitive salary based on experience.")
    assert not s.mentioned


def test_currency_detection_usd():
    s = parse_salary("USD 90,000 per year in New York.")
    assert s.currency == "USD"


def test_healthy_verdict():
    s = parse_salary("$65,000 - $80,000 per year in Toronto")
    checked = salary_sanity_check(s, level="entry", text_hint="Toronto")
    assert checked.verdict == "healthy"


def test_low_verdict():
    s = parse_salary("$30,000 per year in Toronto")
    checked = salary_sanity_check(s, level="entry", text_hint="Toronto")
    assert checked.verdict == "low"


def test_vague_verdict():
    s = parse_salary("competitive salary")
    checked = salary_sanity_check(s, level="entry")
    assert checked.verdict == "vague"


def test_custom_ranges():
    ranges = load_ranges()
    assert "CA" in ranges["ranges"] and "US" in ranges["ranges"]
    custom = {"meta": {}, "ranges": {"CA": {"entry": {"min": 1, "max": 2, "median": 1}}}}
    s = parse_salary("$1,000,000 per year")
    checked = salary_sanity_check(s, level="entry", country="CA", ranges=custom)
    assert checked.verdict == "high"
