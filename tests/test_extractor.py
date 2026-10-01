"""Tests for skill / tech-stack / experience extraction."""

from offersleuth.extractor import detect_level, extract_experience, extract_skills


def test_required_section_skills():
    jd = """## Required
- Java and Spring Boot
- PostgreSQL
## Nice to have
- React
"""
    result = extract_skills(jd)
    assert "Java" in result["required"]
    assert "Spring Boot" in result["required"]
    assert "SQL" in result["required"]
    assert "React" in result["nice_to_have"]
    assert "React" not in result["required"]


def test_alias_matching():
    result = extract_skills("We use ReactJS and k8s daily.")
    assert "React" in result["mentioned"]
    assert "Kubernetes" in result["mentioned"]


def test_no_false_positive_java_in_javascript():
    result = extract_skills("JavaScript and TypeScript only.")
    assert "JavaScript" in result["mentioned"]
    # "java" must not match inside "javascript"
    assert "Java" not in result["mentioned"]


def test_experience_years():
    sig = extract_experience("Need 3+ years of experience with Python.")
    assert 3 in sig.years_mentioned
    assert sig.max_years == 3


def test_level_detection():
    assert detect_level("Junior Software Developer wanted") == "entry"
    assert detect_level("Senior backend engineer") == "senior"
    assert detect_level("A developer role") == "unknown"


def test_categories_present():
    result = extract_skills("Java, Docker, AWS")
    assert result["categories"]["Java"] == "language"
    assert result["categories"]["Docker"] == "devops"
    assert result["categories"]["AWS"] == "cloud"
