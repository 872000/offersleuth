"""Terminal and JSON rendering of an OfferSleuth Report."""

from __future__ import annotations

import json
from dataclasses import asdict

from .models import Report

_SEVERITY_BADGE = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]    ",
    "medium": "[MEDIUM]  ",
    "low": "[LOW]     ",
    "info": "[INFO]    ",
}

_BAR_WIDTH = 30


def render_text(report: Report, show_resume: bool = True) -> str:
    """Render a human-readable terminal report."""
    lines: list[str] = []
    add = lines.append

    add("=" * 64)
    add(f"  OfferSleuth report: {report.title}")
    add("=" * 64)
    filled = int(_BAR_WIDTH * report.score / 100)
    bar = "#" * filled + "-" * (_BAR_WIDTH - filled)
    add(f"  Score: {report.score}/100  [{bar}]  Grade: {report.grade}")
    add("")
    add(f"  {report.summary}")
    add("")

    # Skills
    add("-" * 64)
    add("  SKILLS & TECH STACK")
    add("-" * 64)
    if report.required_skills:
        add("  Required:     " + ", ".join(report.required_skills))
    if report.nice_to_have_skills:
        add("  Nice-to-have: " + ", ".join(report.nice_to_have_skills))
    if not report.required_skills and not report.nice_to_have_skills:
        add("  (no recognizable tech skills found)")
    exp = report.experience
    years = f"max {exp.max_years}y" if exp.max_years else "not specified"
    add(f"  Experience:   level={exp.stated_level}, years {years}")
    add("")

    # Salary
    add("-" * 64)
    add("  SALARY CHECK")
    add("-" * 64)
    s = report.salary
    if s.mentioned:
        rng = f"${s.low:,.0f} - ${s.high:,.0f} {s.currency}/yr"
        add(f"  Found: {rng}  -> verdict: {s.verdict.upper()}")
    else:
        add("  Found: none  -> verdict: VAGUE")
    add(f"  {s.detail}")
    add("")

    # Red flags
    add("-" * 64)
    add(f"  RED FLAGS ({len(report.red_flags)})")
    add("-" * 64)
    if report.red_flags:
        for flag in report.red_flags:
            badge = _SEVERITY_BADGE.get(flag.severity, "[?]       ")
            add(f"  {badge} {flag.title}")
            add(f"             {flag.explanation}")
            if flag.evidence:
                add(f"             evidence: \"{flag.evidence}\"")
    else:
        add("  None detected. Suspiciously clean — or genuinely fine.")
    add("")

    # Resume tailoring
    if show_resume and (report.skill_gaps or report.emphasized_bullets):
        add("-" * 64)
        add("  RESUME TAILORING")
        add("-" * 64)
        for gap in report.skill_gaps:
            mark = "OK " if gap.covered else "GAP"
            add(f"  [{mark}] {gap.skill} ({gap.category})")
        if report.emphasized_bullets:
            add("")
            add("  Bullets to emphasize (most relevant first):")
            for bullet in report.emphasized_bullets[:3]:
                add(f"    * {bullet}")
        add("")

    add("=" * 64)
    return "\n".join(lines)


def render_json(report: Report) -> str:
    """Render the report as JSON (for piping into other tools)."""
    return json.dumps(asdict(report), indent=2)
