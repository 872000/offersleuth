"""Shared data models for OfferSleuth analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RedFlag:
    """A single detected red flag in a job description."""

    rule_id: str
    severity: str  # info | low | medium | high | critical
    title: str
    explanation: str
    evidence: str = ""  # short quote from the JD that triggered the flag


@dataclass
class SalaryCheck:
    """Result of the salary sanity-check."""

    mentioned: bool
    low: float | None = None
    high: float | None = None
    currency: str = "CAD"
    per: str = "year"  # year | hour
    verdict: str = "unknown"  # healthy | low | high | vague | unknown
    detail: str = ""


@dataclass
class SkillGap:
    """A required skill and whether the resume covers it."""

    skill: str
    category: str
    covered: bool


@dataclass
class ExperienceSignal:
    """Years-of-experience requirements found in the JD."""

    years_mentioned: list[int] = field(default_factory=list)
    max_years: int | None = None
    stated_level: str = "unknown"  # entry | junior | mid | senior | unknown


@dataclass
class Report:
    """Full analysis of one job description."""

    title: str
    score: int  # 0-100, higher = healthier posting
    grade: str  # A | B | C | D | F
    required_skills: list[str] = field(default_factory=list)
    nice_to_have_skills: list[str] = field(default_factory=list)
    tech_mentions: list[str] = field(default_factory=list)
    experience: ExperienceSignal = field(default_factory=ExperienceSignal)
    red_flags: list[RedFlag] = field(default_factory=list)
    salary: SalaryCheck = field(default_factory=SalaryCheck)
    skill_gaps: list[SkillGap] = field(default_factory=list)
    emphasized_bullets: list[str] = field(default_factory=list)
    summary: str = ""
