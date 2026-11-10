"""Explicit, versioned vocabulary equivalences. No fuzzy permission expansion."""

import re


def label(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold().replace("_", " "))


MEDIA = {
    "online_advertising": {
        "online advertising",
        "online advertisement",
        "online advertisements",
        "online commercial advertising",
        "online commercial advertisement",
        "online commercial advertisements",
        "internet advertising",
    },
    "television": {"television", "television advertising", "tv advertising", "tv", "broadcast television"},
    "podcast": {"podcast", "podcasts", "podcast advertising", "podcast advertisements"},
    "radio": {"radio", "radio advertising", "broadcast radio"},
    "audiobook": {"audiobook", "audiobooks"},
    "film": {"film", "cinema", "motion picture"},
}
CATEGORIES = {
    "political_advertising": {
        "political advertising",
        "political advertisement",
        "political advertisements",
        "political endorsement",
        "political endorsements",
    },
    "gambling": {"gambling", "gambling advertising", "gambling promotions", "gambling promotion"},
    "adult_content": {"adult content", "adult-content advertising", "adult content advertising"},
}


def canonical(value: str, vocabulary: dict[str, set[str]]) -> str | None:
    normalized = label(value)
    return next(
        (
            key
            for key, aliases in vocabulary.items()
            if normalized in aliases or normalized == key.replace("_", " ")
        ),
        None,
    )


def medium_scope(actual: str, permitted: list[str]) -> str:
    """Allowed exact/known equivalents, violated known distinct media, otherwise uncertain."""
    if "*" in permitted or label(actual) in [label(x) for x in permitted]:
        return "allowed"
    actual_id = canonical(actual, MEDIA)
    rule_ids = [canonical(x, MEDIA) for x in permitted]
    if actual_id and actual_id in rule_ids:
        return "allowed"
    if actual_id and all(rule_ids):
        return "violated"
    return "uncertain"


def territory(value: str) -> str:
    return (
        "us"
        if label(value) in {"us", "usa", "u.s.", "u.s.a.", "united states", "united states of america"}
        else label(value)
    )


def category(value: str) -> str:
    return canonical(value, CATEGORIES) or label(value)
