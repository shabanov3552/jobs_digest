"""Stage-1 filter: regex-match posts that name the role of the active profile.

False positives (articles about the role, courses, memes) are filtered out
later by the rule-based stage-2 filter in enrich.py. This stage is
intentionally permissive.

The patterns come from profiles/<name>.yml (`roles.patterns` and
`roles.loose`); see role_profile.py.

Input:  data/raw_tg.json
Output: data/parsed.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from role_profile import PROFILE

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw_tg.json"
PARSED_PATH = ROOT / "data" / "parsed.json"

# A role that is unambiguously ours, without the loose abbreviations.
ROLE_RE = PROFILE.role_re
# Good enough to let a post in, not to name its role.
VACANCY_RE = PROFILE.vacancy_re

CONFIG_PATH = ROOT / "config" / "sources.yml"
config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
EXCLUDE_POST_RES = [
    re.compile(pattern, re.IGNORECASE | re.UNICODE)
    for pattern in config.get("exclude_posts") or []
]


def matches(text: str) -> bool:
    return bool(VACANCY_RE.search(text or ""))


def is_excluded_post(text: str) -> bool:
    """Whether a whole post starts with a configured exclusion marker."""
    first_line = next((line for line in (text or "").splitlines() if line.strip()), "")
    return any(pattern.search(first_line) for pattern in EXCLUDE_POST_RES)


def run() -> None:
    posts = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    excluded = [p for p in posts if is_excluded_post(p.get("text", ""))]
    matched = [p for p in posts if not is_excluded_post(p.get("text", "")) and matches(p.get("text", ""))]
    for p in matched:
        p["regex_matched"] = True
    PARSED_PATH.write_text(
        json.dumps(matched, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"[parse] excluded {len(excluded)} resume posts; "
        f"{len(matched)}/{len(posts)} posts matched regex -> {PARSED_PATH}"
    )


if __name__ == "__main__":
    run()
