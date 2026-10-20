"""Deterministic grounding guard for agent-written explanations.

The AI layer may only rephrase what the detectors measured. This guard rejects an explanation that
cites a field the insight does not have, makes a claim with no cited field, quotes a number that
cannot be traced to the insight, or names a shirt number of a player the insight does not involve. It needs no model, so it is cheap, repeatable and testable.
"""
import math
import re

from .glossary import COMMON_FIELDS, FIELDS, citable_fields

# Player ids such as H10 or A6, and shirt numbers such as "No. 10", contain digits but are not quantities.
PLAYER_ID = re.compile(r"\b[HA]\d{1,2}\b")
SHIRT = re.compile(r"\b(?:No\.|number|#)\s?(\d{1,2})\b", re.IGNORECASE)
NUMBER = re.compile(r"\d+(?:\.\d+)?")


def quantities(text):
    """The numbers in `text` that state a quantity, ignoring player ids and shirt numbers."""
    return NUMBER.findall(SHIRT.sub("", PLAYER_ID.sub("", text)))


def involved_shirts(insight):
    """Shirt numbers of every player the insight names."""
    ids = [insight.get(k) for k in ("playerId", "markerId", "partnerId")] + insight.get("bypassedIds", [])
    return {int(pid[1:]) for pid in ids if pid}


def _whole(v):
    # Round half up, as a reader would ("14.5 m" is "about 15 m"); round() would give 14.
    return float(math.floor(v + 0.5))


def _field_value(insight, field):
    if field in insight.get("evidence", {}):
        return insight["evidence"][field]
    value = insight.get(field)
    return len(value) if isinstance(value, list) else value


def allowed_numbers(insight, fields):
    """Numbers a claim citing `fields` may quote.

    Each cited value as stored, to one decimal or rounded to a whole number, a cited confidence as a
    percentage, and any number in the cited fields' definitions (such as the 5 s detection window).
    """
    definitions = {**COMMON_FIELDS, **FIELDS.get(insight["type"], {}).get("fields", {})}
    allowed = set()
    for field in fields:
        v = _field_value(insight, field)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            allowed |= {round(v, 2), round(v, 1), _whole(v)}
            if field == "confidence":
                allowed.add(_whole(v * 100))
        allowed |= {float(n) for n in NUMBER.findall(definitions.get(field, ""))}
    return allowed


def _unsupported_numbers(text, allowed):
    return [raw for raw in quantities(text) if float(raw) not in allowed]


def check(insight, explanation):
    """Return a list of problems; an empty list means the explanation is grounded."""
    problems = []
    fields = citable_fields(insight)

    if not explanation.claims:
        problems.append("The explanation makes no claims.")
    for claim in explanation.claims:
        if not claim.evidence:
            problems.append(f'Claim cites no evidence: "{claim.text}"')
        unknown = sorted(set(claim.evidence) - fields)
        if unknown:
            problems.append(f'Claim cites fields the insight does not have ({", ".join(unknown)}): "{claim.text}"')
        # A claim's numbers must come from the fields that claim cites, not just anywhere in the insight.
        for raw in _unsupported_numbers(claim.text, allowed_numbers(insight, claim.evidence)):
            problems.append(f'Number {raw} is not in the fields this claim cites: "{claim.text}"')

    # A shirt number must belong to a player the insight names.
    shirts = involved_shirts(insight)
    for text in [explanation.headline] + [c.text for c in explanation.claims]:
        for raw in SHIRT.findall(text):
            if int(raw) not in shirts:
                problems.append(f'No. {raw} is not a player in this insight: "{text}"')

    # The headline cites nothing, so it may not quote numbers; they belong in cited claims.
    if quantities(explanation.headline):
        problems.append(f'The headline may not quote numbers; put them in a cited claim: "{explanation.headline}"')
    return problems
