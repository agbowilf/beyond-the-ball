"""Deterministic grounding guard for agent-written explanations.

The AI layer may only rephrase what the detectors measured. This guard rejects an explanation that
cites a field the insight does not have, makes a claim with no cited field, or quotes a number that
cannot be traced to the insight. It needs no model, so it is cheap, repeatable and testable.
"""
import math
import re

from .glossary import citable_fields

# Player ids such as H10 or A6 contain digits but are not quantities.
PLAYER_ID = re.compile(r"\b[HA]\d{1,2}\b")
NUMBER = re.compile(r"\d+(?:\.\d+)?")


def _numeric_values(insight):
    values = [insight.get("t"), insight.get("confidence")]
    values += list(insight.get("evidence", {}).values())
    if "bypassedIds" in insight:
        values.append(len(insight["bypassedIds"]))
    return [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]


def _whole(v):
    # Round half up, as a reader would ("14.5 m" is "about 15 m"); round() would give 14.
    return float(math.floor(v + 0.5))


def allowed_numbers(insight):
    """Numbers an explanation may quote: each value as stored, to one decimal, or rounded to a whole number."""
    allowed = set()
    for v in _numeric_values(insight):
        allowed |= {round(v, 2), round(v, 1), _whole(v)}
    if "confidence" in insight:
        allowed.add(_whole(insight["confidence"] * 100))  # quoted as a percentage
    return allowed


def check(insight, explanation):
    """Return a list of problems; an empty list means the explanation is grounded."""
    problems = []
    fields = citable_fields(insight)
    numbers = allowed_numbers(insight)

    if not explanation.claims:
        problems.append("The explanation makes no claims.")
    for claim in explanation.claims:
        if not claim.evidence:
            problems.append(f'Claim cites no evidence: "{claim.text}"')
        unknown = sorted(set(claim.evidence) - fields)
        if unknown:
            problems.append(f'Claim cites fields the insight does not have ({", ".join(unknown)}): "{claim.text}"')

    for text in [explanation.headline] + [c.text for c in explanation.claims]:
        for raw in NUMBER.findall(PLAYER_ID.sub("", text)):
            if float(raw) not in numbers:
                problems.append(f'Number {raw} is not in the insight: "{text}"')
    return problems
