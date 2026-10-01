"""OfferSleuth — job-description analyzer for job seekers.

Detects red flags, sanity-checks salary, extracts skills, and suggests
which resume bullets to tailor for a given posting.

Usable as a CLI::

    python -m offersleuth demo_data/sample_jds/good.md

or as a library::

    import offersleuth
    report = offersleuth.analyze(jd_text)
    print(report.summary)
"""

from .models import Report, RedFlag, SalaryCheck, SkillGap, ExperienceSignal
from .extractor import extract_skills, extract_experience, detect_level
from .redflags import detect_red_flags
from .salary import parse_salary, salary_sanity_check, load_ranges
from .resume import tailor_resume
from .report import analyze

__all__ = [
    "analyze",
    "detect_red_flags",
    "extract_experience",
    "extract_skills",
    "detect_level",
    "load_ranges",
    "parse_salary",
    "salary_sanity_check",
    "tailor_resume",
    "Report",
    "RedFlag",
    "SalaryCheck",
    "SkillGap",
    "ExperienceSignal",
]

__version__ = "0.1.0"
