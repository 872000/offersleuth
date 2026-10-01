"""Tests for resume-bullet tailoring."""

from offersleuth.resume import tailor_resume


BULLETS = [
    "Built REST APIs with Java and Spring Boot serving 10k+ daily requests.",
    "Developed React dashboard components with TypeScript.",
    "Wrote unit tests with JUnit achieving 85% code coverage.",
]


def test_gap_detection():
    gaps, emphasized, suggestions = tailor_resume(BULLETS, ["Java", "Kubernetes"])
    by_skill = {g.skill: g.covered for g in gaps}
    assert by_skill["Java"] is True
    assert by_skill["Kubernetes"] is False


def test_emphasis_ranking():
    gaps, emphasized, suggestions = tailor_resume(BULLETS, ["Java", "Spring Boot"])
    assert emphasized[0] == BULLETS[0]


def test_suggestions_mention_missing_keyword():
    gaps, emphasized, suggestions = tailor_resume(BULLETS, ["Kubernetes"])
    assert any("Kubernetes" in s for s in suggestions)


def test_no_required_skills_advice():
    gaps, emphasized, suggestions = tailor_resume(BULLETS, [])
    assert gaps == [] and emphasized == []
    assert suggestions  # still gives generic advice
