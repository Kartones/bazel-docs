import re
from typing import Dict

FULL_LINE_CLEANUPS = [
    "Project: /_project.yaml",
    "Book: /_book.yaml",
]

REGEX_LINE_CLEANUPS = [
    r"\{% include.*?%}",
    r"\{% dynamic.*?%}",
    r"\{# .*? #\}",
    r" \{\:#.*?\}",
    r"---\n.*?---\n",
]

REPLACEMENTS: Dict[str, str] = {}


def cleanup_content(content: str) -> str:
    for cleanup in FULL_LINE_CLEANUPS:
        content = content.replace(cleanup, "")

    for regex_cleanup in REGEX_LINE_CLEANUPS:
        content = re.sub(regex_cleanup, "", content, flags=re.DOTALL)

    for replacement, replacement_value in REPLACEMENTS.items():
        content = content.replace(replacement, replacement_value)

    prev_content = ""
    while prev_content != content:
        prev_content = content
        content = re.sub(r"\n{3,}", "\n\n", content)

    return content
