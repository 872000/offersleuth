"""Skill, tech-stack and experience extraction from job-description text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ExperienceSignal

# Canonical skill -> list of aliases to match (lowercased).
# Matching is word-boundary aware, so "java" does not match "javascript".
_SKILLS: dict[str, tuple[str, list[str]]] = {
    # (category, [aliases])
    "Java": ("language", ["java"]),
    "Python": ("language", ["python"]),
    "JavaScript": ("language", ["javascript", "js"]),
    "TypeScript": ("language", ["typescript", "ts"]),
    "C++": ("language", ["c++"]),
    "C#": ("language", ["c#"]),
    "Go": ("language", ["golang"]),
    "Kotlin": ("language", ["kotlin"]),
    "Swift": ("language", ["swift"]),
    "PHP": ("language", ["php"]),
    "Ruby": ("language", ["ruby"]),
    "Rust": ("language", ["rust"]),
    "Spring Boot": ("framework", ["spring boot", "springboot", "spring"]),
    "React": ("framework", ["react", "reactjs", "react.js"]),
    "Angular": ("framework", ["angular", "angularjs"]),
    "Vue": ("framework", ["vue", "vuejs", "vue.js"]),
    "Next.js": ("framework", ["next.js", "nextjs"]),
    "Node.js": ("framework", ["node.js", "nodejs", "node"]),
    "Django": ("framework", ["django"]),
    "Flask": ("framework", ["flask"]),
    "FastAPI": ("framework", ["fastapi"]),
    ".NET": ("framework", [".net", "dotnet", "asp.net"]),
    "SQL": ("database", ["sql", "mysql", "postgresql", "postgres"]),
    "MongoDB": ("database", ["mongodb", "mongo"]),
    "Redis": ("database", ["redis"]),
    "Docker": ("devops", ["docker", "containerization"]),
    "Kubernetes": ("devops", ["kubernetes", "k8s"]),
    "CI/CD": ("devops", ["ci/cd", "cicd", "continuous integration"]),
    "Git": ("tools", ["git", "github", "gitlab"]),
    "AWS": ("cloud", ["aws", "amazon web services"]),
    "Azure": ("cloud", ["azure"]),
    "GCP": ("cloud", ["gcp", "google cloud"]),
    "REST": ("concept", ["rest", "restful", "rest api"]),
    "GraphQL": ("concept", ["graphql"]),
    "Microservices": ("concept", ["microservices"]),
    "Agile": ("concept", ["agile", "scrum", "kanban"]),
    "Unit Testing": ("concept", ["unit testing", "junit", "pytest", "jest", "testing"]),
    "Linux": ("tools", ["linux", "unix"]),
    "Jenkins": ("devops", ["jenkins"]),
    "Terraform": ("devops", ["terraform"]),
    "HTML/CSS": ("frontend", ["html", "css"]),
}

# Pre-compile patterns once.
_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        canonical,
        category,
        re.compile(
            r"(?<![\w+#./])(" + "|".join(re.escape(a) for a in aliases) + r")(?![\w+#./])",
            re.IGNORECASE,
        ),
    )
    for canonical, (category, aliases) in _SKILLS.items()
]

_REQUIRED_SECTION = re.compile(
    r"(required|requirements|must[- ]have|what you.?ll bring|qualifications|"
    r"minimum qualifications|what you need|key skills|technical skills)",
    re.IGNORECASE,
)
_NICE_SECTION = re.compile(
    r"(nice[- ]to[- ]have|bonus|preferred|pluses|nice to haves|would be (a )?plus|"
    r"desirable|advantage)",
    re.IGNORECASE,
)
_SECTION_HEADER = re.compile(r"^\s*(#{1,4}\s*)?([A-Z][\w /&,-]{2,40}):?\s*$")


def _looks_like_header(line: str) -> str | None:
    """Return the header text if a line looks like a section header."""
    match = _SECTION_HEADER.match(line)
    if not match:
        return None
    header = match.group(2)
    stripped = line.strip()
    # Markdown headers and colon-terminated lines are unambiguous.
    if stripped.startswith("#") or stripped.endswith(":"):
        return header
    # Bare headers ("Requirements", "Nice to have") are short and comma-free;
    # a line like "Java, Docker, AWS" is content, not a header.
    if "," in header or ";" in header or len(header.split()) > 4:
        return None
    return header


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split a JD into (section_kind, body) chunks.

    section_kind is one of "required", "nice", or "general".
    """
    chunks: list[tuple[str, str]] = []
    current_kind = "general"
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append((current_kind, body))

    for line in text.splitlines():
        header = _looks_like_header(line)
        if header is not None:
            flush()
            current_lines = []
            if _NICE_SECTION.search(header):
                current_kind = "nice"
            elif _REQUIRED_SECTION.search(header):
                current_kind = "required"
            else:
                current_kind = "general"
        else:
            current_lines.append(line)
    flush()
    return chunks


def extract_skills(text: str) -> dict[str, list[str] | dict[str, str]]:
    """Extract skills, split into required / nice-to-have by section context.

    Returns a dict with keys ``required``, ``nice_to_have``, ``mentioned``
    and ``categories`` (skill -> category).
    """
    found: dict[str, set[str]] = {"required": set(), "nice": set(), "general": set()}
    categories: dict[str, str] = {}

    for kind, body in _split_sections(text):
        lowered = body.lower()
        for canonical, category, pattern in _PATTERNS:
            if pattern.search(lowered):
                found[kind].add(canonical)
                categories[canonical] = category

    required = found["required"] | (found["general"] if not found["required"] else set())
    # "mentioned" = everything, deduplicated
    mentioned = found["required"] | found["nice"] | found["general"]
    return {
        "required": sorted(required),
        "nice_to_have": sorted(found["nice"] - required),
        "mentioned": sorted(mentioned),
        "categories": categories,
    }


_YEARS_RE = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+[\w\s-]{0,30}?(?:experience|exp))?",
    re.IGNORECASE,
)
_YEARS_ALT_RE = re.compile(
    r"(?:experience|exp)\s*(?:of|:)?\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)

_LEVEL_KEYWORDS: dict[str, re.Pattern[str]] = {
    "entry": re.compile(r"\b(entry[- ]?level|new grad|recent grad|0[-–]2 years|junior)\b", re.IGNORECASE),
    "junior": re.compile(r"\bjunior\b", re.IGNORECASE),
    "mid": re.compile(r"\b(mid[- ]?level|intermediate)\b", re.IGNORECASE),
    "senior": re.compile(r"\b(senior|sr\.|lead|principal|staff)\b", re.IGNORECASE),
}


def extract_experience(text: str) -> ExperienceSignal:
    """Find years-of-experience requirements and the stated seniority level."""
    years: set[int] = set()
    for pattern in (_YEARS_RE, _YEARS_ALT_RE):
        for match in pattern.finditer(text):
            years.add(int(match.group(1)))

    level = "unknown"
    for name, pattern in _LEVEL_KEYWORDS.items():
        if pattern.search(text):
            level = name
            break

    sorted_years = sorted(years)
    return ExperienceSignal(
        years_mentioned=sorted_years,
        max_years=max(sorted_years) if sorted_years else None,
        stated_level=level,
    )


def detect_level(text: str) -> str:
    """Shorthand: return just the stated seniority level."""
    return extract_experience(text).stated_level
