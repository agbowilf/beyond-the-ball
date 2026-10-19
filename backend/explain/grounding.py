"""Deterministic grounding guard for agent-written explanations.

The AI layer may only rephrase what the detectors measured. This guard rejects an explanation that
cites a field the insight does not have, makes a claim with no cited field, or quotes a number that
cannot be traced to the insight. It needs no model, so it is cheap, repeatable and testable.
"""
import math
import re

from .glossary import COMMON_FIELDS, FIELDS, citable_fields

# Player ids such as H10 or A6 contain digits but are not quantities.
PLAYER_ID = re.compile(r"\b[HA]\d{1,2}\b")
NUMBER = re.compile(r"\d+(?:\.\d+)?")


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
    return [raw for raw in NUMBER.findall(PLAYER_ID.sub("", text)) if float(raw) not in allowed]


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

    # The headline cites nothing, so its numbers may come from any field.
    for raw in _unsupported_numbers(explanation.headline, allowed_numbers(insight, fields)):
        problems.append(f'Number {raw} is not in the insight: "{explanation.headline}"')
    return problems
