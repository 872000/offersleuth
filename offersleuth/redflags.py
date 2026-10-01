"""Red-flag detector: pattern-based rules with severity and explanations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ExperienceSignal, RedFlag


@dataclass
class _Rule:
    rule_id: str
    severity: str
    title: str
    explanation: str
    patterns: tuple[str, ...]
    negative: tuple[str, ...] = ()  # patterns that cancel the flag


_RULES: list[_Rule] = [
    _Rule(
        rule_id="hero_culture",
        severity="high",
        title="Hero-culture language (rockstar / ninja / guru)",
        explanation=(
            "Postings that ask for a 'rockstar', 'ninja' or 'guru' usually signal "
            "a culture of overwork and vague expectations instead of a clear role."
        ),
        patterns=(r"\brockstar\b", r"\bninja\b", r"\bguru\b", r"\bunicorn\b", r"\bwizard\b"),
    ),
    _Rule(
        rule_id="crunch_culture",
        severity="medium",
        title="'Fast-paced environment' crunch signal",
        explanation=(
            "'Fast-paced environment' is one of the most common euphemisms for "
            "chronic overtime and understaffing. Ask what a typical sprint looks like."
        ),
        patterns=(r"\bfast[- ]paced\b", r"\bhigh[- ]pressure\b", r"\bwear many hats\b"),
    ),
    _Rule(
        rule_id="family_culture",
        severity="medium",
        title="'We're a family' boundary-blurring",
        explanation=(
            "Companies that call themselves a 'family' often expect loyalty without "
            "boundaries — unpaid overtime, guilt about time off, layoffs framed as betrayal."
        ),
        patterns=(r"\bwe'?re a family\b", r"\bwork hard,? play hard\b", r"\bwork hard play hard\b"),
    ),
    _Rule(
        rule_id="mlm_pyramid",
        severity="critical",
        title="Possible MLM / pyramid-scheme phrasing",
        explanation=(
            "Phrases like 'be your own boss', 'unlimited earning potential' and recruiting "
            "language are hallmarks of multi-level marketing schemes, not salaried jobs."
        ),
        patterns=(
            r"\bbe your own boss\b",
            r"\bunlimited earning potential\b",
            r"\bpassive income\b",
            r"\bfinancial freedom\b",
            r"\bground floor opportunity\b",
            r"\brecruit (your|a) (team|downline)\b",
        ),
    ),
    _Rule(
        rule_id="commission_only",
        severity="critical",
        title="Commission-only / no base pay",
        explanation=(
            "Commission-only roles shift all income risk onto you. For an advertised "
            "salaried position this is a major red flag."
        ),
        patterns=(r"\bcommission[- ]only\b", r"\b100%\s*commission\b", r"\bno base salary\b"),
    ),
    _Rule(
        rule_id="unpaid_trial",
        severity="critical",
        title="Unpaid trial work or 'test projects'",
        explanation=(
            "Unpaid 'trial shifts' or large take-home projects are often free labour. "
            "Legitimate hiring uses short, bounded, paid assessments."
        ),
        patterns=(
            r"\bunpaid trial\b",
            r"\btrial (period|shift) (is )?unpaid\b",
            r"\bwork for free\b",
            r"\bvolunteer.{0,20}(position|role)\b",
        ),
    ),
    _Rule(
        rule_id="pay_to_work",
        severity="critical",
        title="Asks you to pay for the job",
        explanation=(
            "Any 'training fee', 'starter kit' or deposit you must pay is a scam. "
            "Real employers pay you."
        ),
        patterns=(
            r"\btraining fee\b",
            r"\bstarter kit\b",
            r"\bpay.{0,20}(deposit|fee).{0,20}(to (start|join)|before)",
        ),
    ),
    _Rule(
        rule_id="always_on",
        severity="high",
        title="Always-on availability demanded",
        explanation=(
            "Requiring 24/7 availability or regular weekend work in the posting itself "
            "means burnout is built into the job description."
        ),
        patterns=(
            r"\b24/7\b",
            r"\bavailable (at all times|around the clock)\b",
            r"\bweekends (required|expected|mandatory)\b",
            r"\bovertime (required|expected|mandatory)\b",
        ),
    ),
    _Rule(
        rule_id="vague_duties",
        severity="medium",
        title="Suspiciously vague about actual duties",
        explanation=(
            "If the posting can't describe what you'd actually do day-to-day, the role "
            "may not exist as advertised — or duties are assigned arbitrarily."
        ),
        patterns=(
            r"\bvarious duties\b",
            r"\bduties as assigned\b",
            r"\bother duties as needed\b",
            r"\bto be discussed\b",
        ),
    ),
    _Rule(
        rule_id="excessive_education",
        severity="low",
        title="Credential gatekeeping",
        explanation=(
            "Demanding a specific elite degree for a generalist role filters candidates "
            "on pedigree rather than ability."
        ),
        patterns=(
            r"\btop[- ]tier university\b",
            r"\bivy league\b",
            r"\bdegree from a prestigious\b",
        ),
    ),
    _Rule(
        rule_id="age_coded",
        severity="low",
        title="Age-coded language",
        explanation=(
            "Terms like 'digital native' or 'young and energetic team' can signal "
            "age discrimination, whether intentional or not."
        ),
        patterns=(r"\bdigital native\b", r"\byoung and energetic\b", r"\brecent graduate only\b"),
    ),
    _Rule(
        rule_id="contractor_misclass",
        severity="medium",
        title="Possible contractor misclassification",
        explanation=(
            "Full-time hours and duties labelled as 'contractor' / '1099' often mean "
            "no benefits, no overtime protection and no job security."
        ),
        patterns=(
            r"\b1099\b",
            r"\bindependent contractor.{0,40}full[- ]time\b",
            r"\bcontractor.{0,40}40\s*hours\b",
        ),
    ),
]

_NO_SALARY = RedFlag(
    rule_id="no_salary",
    severity="medium",
    title="No salary or pay range disclosed",
    explanation=(
        "The posting gives no compensation figure. In several Canadian provinces and "
        "US states pay transparency is required or expected — silence lets employers "
        "anchor low. Ask for the range before investing interview time."
    ),
)


def _compile(rule: _Rule) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, re.IGNORECASE) for p in rule.patterns)


_COMPILED: list[tuple[_Rule, tuple[re.Pattern[str], ...]]] = [
    (rule, _compile(rule)) for rule in _RULES
]


def detect_red_flags(
    text: str,
    experience: ExperienceSignal | None = None,
    salary_mentioned: bool = False,
) -> list[RedFlag]:
    """Run all red-flag rules over the JD text.

    Args:
        text: Raw job-description text.
        experience: Optional parsed experience signals, used for the
            excessive-requirements rule.
        salary_mentioned: Whether a salary figure was found in the text.
    """
    flags: list[RedFlag] = []
    seen: set[str] = set()

    for rule, patterns in _COMPILED:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                cancelled = any(
                    re.search(neg, text, re.IGNORECASE) for neg in rule.negative
                )
                if not cancelled and rule.rule_id not in seen:
                    flags.append(
                        RedFlag(
                            rule_id=rule.rule_id,
                            severity=rule.severity,
                            title=rule.title,
                            explanation=rule.explanation,
                            evidence=match.group(0).strip()[:80],
                        )
                    )
                    seen.add(rule.rule_id)
                break

    # Structural rules that need parsed signals, not just patterns.
    if experience is not None:
        flags.extend(_experience_flags(experience, text))

    if not salary_mentioned:
        flags.append(_NO_SALARY)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    flags.sort(key=lambda f: severity_order.get(f.severity, 5))
    return flags


def _experience_flags(experience: ExperienceSignal, text: str) -> list[RedFlag]:
    flags: list[RedFlag] = []
    if experience.stated_level in ("entry", "junior") and experience.max_years:
        if experience.max_years >= 5:
            flags.append(
                RedFlag(
                    rule_id="excessive_requirements",
                    severity="high",
                    title="Excessive requirements for an entry-level role",
                    explanation=(
                        f"Advertised as {experience.stated_level}-level but asks for "
                        f"{experience.max_years}+ years of experience. Either the level "
                        "or the requirements are mislabelled — expect senior workload "
                        "at junior pay."
                    ),
                    evidence=f"{experience.max_years} years",
                )
            )
        elif experience.max_years >= 3:
            flags.append(
                RedFlag(
                    rule_id="experience_stretch",
                    severity="low",
                    title="Experience ask is a stretch for the level",
                    explanation=(
                        f"Advertised as {experience.stated_level}-level but wants "
                        f"{experience.max_years} years. Often negotiable — apply anyway "
                        "if you meet most of it."
                    ),
                    evidence=f"{experience.max_years} years",
                )
            )

    # Absurd skill count: 15+ distinct tech skills for a junior role.
    if experience.stated_level in ("entry", "junior"):
        skill_count = len(re.findall(r"\b(Java|Python|React|Angular|Vue|Node|AWS|Docker|Kubernetes|SQL|Go|Rust|C\+\+|TypeScript|Spring|Django|Flask)\b", text))
        if skill_count >= 15:
            flags.append(
                RedFlag(
                    rule_id="laundry_list",
                    severity="medium",
                    title="Laundry-list requirements",
                    explanation=(
                        f"Lists ~{skill_count} distinct technologies for a "
                        f"{experience.stated_level}-level role. This is usually a "
                        "wish list, not a real bar — but it also hints at unclear priorities."
                    ),
                )
            )
    return flags
