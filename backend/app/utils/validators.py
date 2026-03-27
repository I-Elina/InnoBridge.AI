import re

VALID_DESIGNATIONS = [
    "school student",
    "college student",
    "final year",
    "professional",
    "research aspirant",
]

VALID_SKILL_LEVELS = ["beginner", "intermediate", "advanced"]


def validate_email(email: str) -> str:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    email = email.strip().lower()
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: '{email}'")
    return email


def validate_designation(designation: str) -> str:
    designation = designation.strip().lower()
    if designation not in VALID_DESIGNATIONS:
        raise ValueError(
            f"Invalid designation '{designation}'. Must be one of: {VALID_DESIGNATIONS}"
        )
    return designation


def validate_skill_level(skill_level: str) -> str:
    skill_level = skill_level.strip().lower()
    if skill_level not in VALID_SKILL_LEVELS:
        raise ValueError(
            f"Invalid skill_level '{skill_level}'. Must be one of: {VALID_SKILL_LEVELS}"
        )
    return skill_level


def validate_interests(interests: list) -> list:
    if not interests or not isinstance(interests, list):
        raise ValueError("interests must be a non-empty array")
    cleaned = [i.strip() for i in interests if isinstance(i, str) and i.strip()]
    if not cleaned:
        raise ValueError("interests must contain at least one non-empty string")
    return cleaned