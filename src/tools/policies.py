"""Find the parts of data/policies that answer a customer question."""

import re
from dataclasses import dataclass
from pathlib import Path

from config import POLICIES_DIR

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    """
    a an the do you is on for my i can what how much to of and or with it in at
    be we your me please does cost are there am was were this that
    """.split()
)
_ALIASES = (
    frozenset({"hire", "rent", "rental", "rented"}),
    frozenset({"bicycle", "bike", "bikes"}),
    frozenset({"ebike", "electric"}),
    frozenset({"child", "children", "kid", "kids"}),
    frozenset({"childseat", "childseats"}),
)
_NO_MATCH = (
    "No policy section matches this question. "
    "Contact the staff at help@citywheels.example or +48 000 000 000."
)
_MAX_SECTIONS = 3


@dataclass(frozen=True)
class Section:
    """One markdown section, kept as written in the policy file."""

    source: str
    heading: str
    body: str
    preamble: str


def search_policies(query: str, policies_dir: Path | None = None) -> str:
    """Return policy excerpts relevant to `query`, or an error string."""
    directory = POLICIES_DIR if policies_dir is None else policies_dir
    try:
        sections = _load_sections(directory)
    except (OSError, UnicodeError) as exc:
        return f"Could not read policies: {exc}"
    chosen = _rank(query, sections)[:_MAX_SECTIONS]
    if not chosen:
        return _NO_MATCH
    return _render(chosen)


def _load_sections(directory: Path) -> list[Section]:
    if not directory.is_dir():
        raise FileNotFoundError(f"policy directory not found: {directory}")
    sections: list[Section] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        sections.extend(_split_sections(path.name, text))
    return sections


def _split_sections(source: str, text: str) -> list[Section]:
    preamble_lines: list[str] = []
    preamble = ""
    heading: str | None = None
    body: list[str] = []
    sections: list[Section] = []

    def close() -> None:
        nonlocal heading, body
        if heading is None:
            return
        sections.append(Section(source, heading, "\n".join(body).strip(), preamble))
        heading = None
        body = []

    for line in text.splitlines():
        if line.startswith("## "):
            close()
            if preamble == "":
                preamble = "\n".join(preamble_lines).strip()
            heading = line.removeprefix("## ").strip()
        elif heading is None:
            preamble_lines.append(line)
        else:
            body.append(line)
    close()
    return sections


def _rank(query: str, sections: list[Section]) -> list[Section]:
    terms = _query_terms(query)
    if not terms:
        return []
    scored: list[tuple[int, str, int, Section]] = []
    for index, section in enumerate(sections):
        tokens = _tokens(f"{section.heading}\n{section.body}")
        score = sum(1 for term in terms if _matches(term, tokens))
        if score:
            scored.append((score, section.source, index, section))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [item[3] for item in scored]


def _render(sections: list[Section]) -> str:
    parts: list[str] = []
    shown_preamble: set[str] = set()
    for section in sections:
        if section.preamble and section.source not in shown_preamble:
            parts.append(section.preamble)
            shown_preamble.add(section.source)
        parts.append(f"# {section.source} — {section.heading}\n\n{section.body}")
    return "\n\n".join(parts)


def _query_terms(query: str) -> list[str]:
    terms: list[str] = []
    for token in sorted(_tokens(query)):
        if token in _STOP or token.isdigit() or token in terms:
            continue
        terms.append(token)
    return terms


def _tokens(text: str) -> set[str]:
    normalized = text.casefold()
    normalized = normalized.replace("e-bike", "ebike")
    normalized = normalized.replace("child seat", "childseat")
    normalized = normalized.replace("child_seat", "childseat")
    return set(_TOKEN.findall(normalized))


def _matches(term: str, tokens: set[str]) -> bool:
    for form in _forms(term):
        for token in tokens:
            if form == token:
                return True
            if len(form) >= 3 and len(token) >= 3 and (token.startswith(form) or form.startswith(token)):
                return True
    return False


def _forms(token: str) -> frozenset[str]:
    for group in _ALIASES:
        if token in group:
            return group
    return frozenset({token})
