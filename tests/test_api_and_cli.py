"""End-to-end tests: public API, report pipeline, CLI and bundled demo data."""

import json
from pathlib import Path

import offersleuth
from offersleuth import analyze
from offersleuth.cli import main
from offersleuth.render import render_json, render_text

ROOT = Path(__file__).resolve().parent.parent
DEMO_JDS = ROOT / "demo_data" / "sample_jds"


def test_public_api_surface():
    for name in ["analyze", "detect_red_flags", "extract_skills", "tailor_resume", "parse_salary"]:
        assert callable(getattr(offersleuth, name)), name


def test_version_present():
    assert offersleuth.__version__


def test_good_jd_scores_well():
    report = analyze((DEMO_JDS / "good.md").read_text(), title="good")
    assert report.grade in ("A", "B")
    assert report.salary.verdict == "healthy"
    assert "Java" in report.required_skills


def test_mediocre_jd_scores_mid():
    report = analyze((DEMO_JDS / "mediocre.md").read_text(), title="mediocre")
    assert report.grade in ("C", "D")
    assert any(f.rule_id == "crunch_culture" for f in report.red_flags)


def test_scammy_jd_scores_poor():
    report = analyze((DEMO_JDS / "scammy.md").read_text(), title="scammy")
    assert report.grade == "F"
    assert any(f.severity == "critical" for f in report.red_flags)


def test_demo_data_files_exist():
    for name in ("good.md", "mediocre.md", "scammy.md"):
        assert (DEMO_JDS / name).exists()
    assert (ROOT / "demo_data" / "sample_resume.txt").exists()
    assert (ROOT / "demo_data" / "salary_ranges.json").exists()


def test_render_text_contains_sections(capsys):
    report = analyze("Junior dev. Java required. Salary $70,000.", title="t")
    out = render_text(report)
    for section in ("SKILLS", "SALARY CHECK", "RED FLAGS", "OfferSleuth score"):
        assert section in out


def test_render_json_is_valid():
    report = analyze("Junior dev. Java required. Salary $70,000.", title="t")
    data = json.loads(render_json(report))
    assert data["title"] == "t" and "score" in data


def test_cli_demo_runs(capsys):
    assert main(["demo", "good"]) == 0
    out = capsys.readouterr().out
    assert "OfferSleuth report" in out


def test_cli_file_arg(capsys):
    assert main([str(DEMO_JDS / "good.md")]) == 0
    assert "OfferSleuth score" in capsys.readouterr().out


def test_cli_jd_text_and_json(capsys):
    assert main(["--jd", "Java developer. Salary $70,000.", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["salary"]["mentioned"] is True
