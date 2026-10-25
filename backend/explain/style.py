"""Audience style rules, checked in code so fan, coach and analyst versions stay clearly different.

The grounding guard decides whether an explanation is true; these rules decide whether it suits its
reader. Problems found here go back to the explainer like any other.
"""
import re

from .glossary import COMMON_FIELDS, FIELDS
from .grounding import quantities

# Words a casual fan should not have to decode.
FAN_JARGON = ("cosine", "displacement", "progression", "bypass", "coefficient", "metric", "detector",
              "confidence", "evidence", "line-breaking", "receiving zone", "marker")
# Praise or criticism is a judgement the detectors never made, so no audience may use it.
JUDGEMENT = ("clever", "brilliant", "great", "superb", "smart", "excellent", "perfect", "genius", "world-class",
             "poor", "lazy", "sloppy", "terrible", "effectively", "masterful", "inch-perfect", "significant",
             "significantly", "precise", "perfectly", "dramatically", "massively",
             "substantial", "substantially", "huge", "hugely")
# Positions are never measured; "defender" alone is fine, as it only says which side a player was on, and so is
# "back line" / "defensive line", which backLineDropM measures.
ROLES = ("midfield", "midfielder", "centre-back", "center-back", "full-back", "fullback", "winger", "striker",
         "back four", "duo")  # "back line" is measured (backLineDropM), so it is allowed
# Raw field names (camelCase) and enum codes belong in the data, not the text. Plain-word field names
# such as "confidence" or "pattern" are ordinary English and allowed.
RAW_TERMS = sorted(
    {k for k in {k for spec in FIELDS.values() for k in spec["fields"]} | set(COMMON_FIELDS) if k != k.lower()}
    | {"ONE_TWO", "LINE_BREAKING_PASS"}
)
WORD = re.compile(r"[A-Za-z0-9'’.-]+")

RULES = {
    "fan": {"claims": (1, 2), "max_words": 20, "headline_words": 10, "max_numbers_total": 1},
    "coach": {"claims": (3, 3), "max_words": 30, "headline_words": 12, "max_numbers_per_claim": 2},
    "analyst": {"claims": (3, 4), "max_words": 35, "headline_words": 12, "min_numbers_per_claim": 1},
}


def _words(text):
    return len(WORD.findall(text))


def check_team_names(explanation, teams, attacking):
    """Teams must be named by their real names, and players credited to the right team.

    `teams` maps our labels (HOME/AWAY) to real names; `attacking` is the label of the team that made the play.
    """
    names = {label: name.split(" (")[0] for label, name in teams.items() if name}
    defending = "AWAY" if attacking == "HOME" else "HOME"
    attackers, defenders = ("H", "A") if attacking == "HOME" else ("A", "H")
    problems = []
    for text in [explanation.headline] + [c.text for c in explanation.claims]:
        rest = text
        for name in sorted(names.values(), key=len, reverse=True):
            rest = rest.replace(name, "")
        # Capitalised "Home"/"Away" (as in "Home's H10") or "home/away team/side"; ordinary "away from" is fine.
        if re.search(r"\b(Home|Away)\b", rest) or re.search(r"\b(home|away) (team|side)\b", rest, re.IGNORECASE):
            problems.append(f'Use the team names ({" / ".join(names.values())}), not "home" or "away": "{text}"')
        for label, wrong in ((defending, attackers), (attacking, defenders)):
            name = names.get(label)
            if name and re.search(rf"{re.escape(name)}[’']s\s+(?:player\s+|defender\s+)?{wrong}\d", text):
                problems.append(f'Player credited to the wrong team ({name}): "{text}"')
    return problems


def check_pattern(insight, explanation):
    """Wording that contradicts the measured pattern of a Sequence Origin insight."""
    if insight.get("type") != "SEQUENCE_ORIGIN":
        return []
    problems = []
    for text in [explanation.headline] + [c.text for c in explanation.claims]:
        low = text.lower()
        if insight.get("pattern") == "LINE_BREAKING_PASS" and re.search(
                r"\breturn(ed|s)?\b|one-two|one two|passed back|played back|sent back|back to", low):
            problems.append(f'This was a single pass with no return or one-two; describe only that pass: "{text}"')
        if re.search(r"\bdefenders?\b", low):
            problems.append(f'Bypassed players were opponents in any position; say opponents or players: "{text}"')
    return problems


def check_style(audience, explanation, real_data=False):
    """Return a list of style problems for this audience; empty means it fits.

    For real data, player numbers are converter labels, so shirt-number phrasing ("No. 10") is rejected.
    """
    rules = RULES[audience]
    problems = []
    claims = [c.text for c in explanation.claims]

    low, high = rules["claims"]
    if not low <= len(claims) <= high:
        wanted = f"exactly {low}" if low == high else f"{low} to {high}"
        problems.append(f"Use {wanted} claims for a {audience}; there are {len(claims)}.")
    if _words(explanation.headline) > rules["headline_words"]:
        problems.append(f"The headline has {_words(explanation.headline)} words; a {audience} headline may have at "
                        f'most {rules["headline_words"]}: "{explanation.headline}"')
    for text in claims:
        if not text.rstrip().endswith((".", "!", "?")):
            problems.append(f'Each claim must be a complete sentence ending with a full stop: "{text}"')
        if _words(text) > rules["max_words"]:
            problems.append(f'This sentence has {_words(text)} words; use at most {rules["max_words"]} for a '
                            f'{audience}: "{text}"')
    for text in [explanation.headline] + claims:
        judged = [w for w in JUDGEMENT if re.search(rf"\b{re.escape(w)}\b", text.lower())]
        if judged:
            problems.append(f'Remove praise or criticism the data does not measure ({", ".join(judged)}): "{text}"')
        roles = [w for w in ROLES if re.search(rf"\b{re.escape(w)}\b", text.lower())]
        if roles:
            problems.append(f'Player positions were not measured; remove ({", ".join(roles)}): "{text}"')
        raw = [w for w in RAW_TERMS if re.search(rf"\b{re.escape(w)}\b", text)]
        if raw:
            problems.append(f'Write in words, not field names or codes ({", ".join(raw)}): "{text}"')

    if audience == "fan":
        numbers = sum(len(quantities(t)) for t in [explanation.headline] + claims)
        if numbers > rules["max_numbers_total"]:
            problems.append(f"A fan explanation may quote at most one number in total; this one quotes {numbers}. "
                            "Describe the rest in plain words.")
        for text in [explanation.headline] + claims:
            jargon = [w for w in FAN_JARGON if re.search(rf"\b{re.escape(w)}\b", text.lower())]
            if jargon:
                problems.append(f'Avoid jargon a casual fan would not use ({", ".join(jargon)}): "{text}"')
    if audience == "coach":
        for text in claims:
            count = len(quantities(text))
            if count > rules["max_numbers_per_claim"]:
                problems.append(f"This sentence quotes {count} numbers; a coach sentence may quote at most two. "
                                f'Split it, or say one of them in words: "{text}"')
    if audience == "analyst":
        for text in claims:
            if len(quantities(text)) < rules["min_numbers_per_claim"]:
                problems.append(f'Each analyst sentence should quote at least one measurement: "{text}"')
    if real_data:
        for text in [explanation.headline] + claims:
            if re.search(r"\b(?:No\.|number|#)\s?\d", text, re.IGNORECASE):
                problems.append(f'Player numbers here are labels, not shirt numbers; use ids such as H10: "{text}"')
    return problems
