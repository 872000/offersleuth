"""Resume-bullet tailoring: match resume bullets against a JD's required skills."""

from __future__ import annotations

import re

from .models import SkillGap


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _skill_in_text(skill: str, text: str) -> bool:
    """Word-boundary aware check that a resume covers a skill."""
    lowered = _normalize(text)
    pattern = re.compile(r"(?<![\w+#./])" + re.escape(skill.lower()) + r"(?![\w+#./])")
    if pattern.search(lowered):
        return True
    # Alias fallback for common compound skills.
    aliases = {
        "git": ["github", "gitlab"],
        "spring boot": ["spring"],
        "ci/cd": ["cicd", "continuous integration", "jenkins", "github actions"],
        "unit testing": ["junit", "pytest", "jest", "testing"],
        "sql": ["mysql", "postgresql", "database"],
        "html/css": ["html", "css", "frontend"],
    }
    for alias in aliases.get(skill.lower(), []):
        if re.search(r"(?<![\w+#./])" + re.escape(alias) + r"(?![\w+#./])", lowered):
            return True
    return False


def tailor_resume(
    bullets: list[str], required_skills: list[str], categories: dict[str, str] | None = None
) -> tuple[list[SkillGap], list[str], list[str]]:
    """Analyze resume bullets against required skills.

    Returns:
        gaps: SkillGap list (skill, category, covered).
        emphasized: bullets worth leading with, most JD-relevant first.
        suggestions: human-readable keyword-gap advice strings.
    """
    categories = categories or {}
    gaps = [
        SkillGap(
            skill=skill,
            category=categories.get(skill, "general"),
            covered=any(_skill_in_text(skill, b) for b in bullets),
        )
        for skill in required_skills
    ]

    # Rank bullets by how many required skills they mention.
    scored: list[tuple[int, str]] = []
    for bullet in bullets:
        hits = sum(1 for skill in required_skills if _skill_in_text(skill, bullet))
        scored.append((hits, bullet))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    emphasized = [bullet for hits, bullet in scored if hits > 0]

    missing = [g.skill for g in gaps if not g.covered]
    suggestions: list[str] = []
    if missing:
        suggestions.append(
            "Keyword gaps to close: " + ", ".join(missing) + ". "
            "If you have any experience with these, add a bullet naming them explicitly — "
            "ATS scanners and recruiters both match on exact terms."
        )
    covered = [g.skill for g in gaps if g.covered]
    if covered:
        suggestions.append(
            "Already covered: " + ", ".join(covered) + ". "
            "Move these terms toward the top of each bullet so they survive the 6-second skim."
        )
    if emphasized:
        suggestions.append(
            f"Lead with bullet: \"{_truncate(emphasized[0])}\" — it hits the most "
            "required keywords for this posting."
        )
    if not required_skills:
        suggestions.append(
            "No concrete technical requirements found in this posting, so there's "
            "nothing specific to mirror. Keep bullets outcome-focused."
        )
    return gaps, emphasized, suggestions


def _truncate(text: str, limit: int = 90) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
