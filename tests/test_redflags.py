"""Tests for the red-flag detector."""

from offersleuth.extractor import extract_experience
from offersleuth.redflags import detect_red_flags


def test_hero_culture_flag():
    flags = detect_red_flags("We need a rockstar developer to join our team!")
    assert any(f.rule_id == "hero_culture" and f.severity == "high" for f in flags)


def test_mlm_flag_is_critical():
    flags = detect_red_flags("Be your own boss with unlimited earning potential!")
    mlm = [f for f in flags if f.rule_id == "mlm_pyramid"]
    assert mlm and mlm[0].severity == "critical"


def test_unpaid_trial_flag():
    flags = detect_red_flags("The unpaid trial shift lasts two weeks.")
    assert any(f.rule_id == "unpaid_trial" for f in flags)


def test_commission_only_flag():
    flags = detect_red_flags("This is a 100% commission-only opportunity.")
    assert any(f.rule_id == "commission_only" for f in flags)


def test_crunch_signal_flag():
    flags = detect_red_flags("Join our fast-paced environment today.")
    assert any(f.rule_id == "crunch_culture" for f in flags)


def test_no_salary_flag_when_missing():
    flags = detect_red_flags("Great role. Apply now.", salary_mentioned=False)
    assert any(f.rule_id == "no_salary" for f in flags)


def test_no_salary_flag_absent_when_present():
    flags = detect_red_flags("Salary: $70,000 per year.", salary_mentioned=True)
    assert not any(f.rule_id == "no_salary" for f in flags)


def test_excessive_requirements_for_entry_level():
    exp = extract_experience("Entry-level role. Requires 5+ years of experience.")
    flags = detect_red_flags("Entry-level role.", experience=exp)
    assert any(f.rule_id == "excessive_requirements" for f in flags)


def test_clean_posting_has_no_flags():
    flags = detect_red_flags(
        "Junior developer. Salary $65,000. Java and Spring Boot required.",
        salary_mentioned=True,
    )
    assert flags == []


def test_flags_sorted_by_severity():
    flags = detect_red_flags(
        "Be your own boss! We need a ninja for our fast-paced environment."
    )
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    severities = [order[f.severity] for f in flags]
    assert severities == sorted(severities)
