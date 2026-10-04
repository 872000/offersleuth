"""Orchestrates the full OfferSleuth analysis pipeline."""

from __future__ import annotations

from . import extractor, redflags, resume as resume_mod, salary as salary_mod
from .models import Report, SalaryCheck

_SEVERITY_COST = {"critical": 30, "high": 15, "medium": 8, "low": 3, "info": 1}


def analyze(
    text: str,
    title: str = "Untitled posting",
    resume_bullets: list[str] | None = None,
    country: str | None = None,
    ranges: dict | None = None,
) -> Report:
    """Run the full analysis pipeline on one job-description text."""
    skills = extractor.extract_skills(text)
    experience = extractor.extract_experience(text)
    salary = salary_mod.parse_salary(text)
    salary = salary_mod.salary_sanity_check(
        salary,
        level=experience.stated_level if experience.stated_level != "unknown" else "entry",
        country=country,
        text_hint=text,
        ranges=ranges,
    )
    flags = redflags.detect_red_flags(
        text, experience=experience, salary_mentioned=salary.mentioned
    )

    gaps, emphasized, suggestions = ([], [], [])
    if resume_bullets:
        gaps, emphasized, suggestions = resume_mod.tailor_resume(
            resume_bullets, skills["required"], skills["categories"]
        )

    score = max(0, 100 - sum(_SEVERITY_COST.get(f.severity, 5) for f in flags))
    grade = _grade(score)
    summary = _summarize(title, score, grade, flags, salary, gaps)

    return Report(
        title=title,
        score=score,
        grade=grade,
        required_skills=skills["required"],
        nice_to_have_skills=skills["nice_to_have"],
        tech_mentions=skills["mentioned"],
        experience=experience,
        red_flags=flags,
        salary=salary,
        skill_gaps=gaps,
        emphasized_bullets=emphasized,
        summary=summary,
    )


def _grade(score: int) -> str:
    """Map a 0-100 posting score to a letter grade (A/F scale)."""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _summarize(title, score, grade, flags, salary: SalaryCheck, gaps) -> str:
    """Build the one-paragraph plain-English verdict for the report.

    Combines the letter grade, red-flag severity counts, salary disclosure,
    and resume keyword gaps into a triage summary for a posting.
    """
    critical = sum(1 for f in flags if f.severity == "critical")
    high = sum(1 for f in flags if f.severity == "high")
    missing = [g.skill for g in gaps if not g.covered] if gaps else []

    if critical:
        verdict = "Walk away — critical red flags detected."
    elif grade in ("A", "B") and not high:
        verdict = "Looks legit — worth applying."
    elif high:
        verdict = "Proceed with caution — notable red flags."
    else:
        verdict = "Mediocre posting — apply only if the role itself excites you."

    parts = [f"OfferSleuth score {score}/100 (grade {grade}): {verdict}"]
    if salary.mentioned:
        parts.append(f"Salary: {salary.detail}")
    else:
        parts.append("Salary: not disclosed.")
    if missing:
        parts.append("Resume keyword gaps: " + ", ".join(missing) + ".")
    return " ".join(parts)
