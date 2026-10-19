import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.explain.grounding import check  # noqa: E402
from backend.explain.models import Claim, Explanation  # noqa: E402

INSIGHTS = json.loads((ROOT / "scenarios" / "01_decoy_run.insights.json").read_text())
SPACE = next(i for i in INSIGHTS if i["type"] == "SPACE_CREATOR")
ORIGIN = next(i for i in INSIGHTS if i["type"] == "SEQUENCE_ORIGIN")


def _explanation(*claims, headline="H10's decoy run opened the space"):
    return Explanation(headline=headline, claims=[Claim(text=t, evidence=e) for t, e in claims])


def test_grounded_explanation_passes():
    exp = _explanation(
        ("H10 ran 14.5 m off the ball and A6 followed.", ["runnerDisplacementM", "markerId"]),
        ("A6 ended 11.1 m from where H11 received, up from 5.0 m.",
         ["markerDistanceToTargetEndM", "markerDistanceToTargetStartM"]),
        ("The detector is 90% confident.", ["confidence"]),
    )
    assert check(SPACE, exp) == []


def test_rounded_numbers_are_allowed():
    exp = _explanation(("H10 ran about 15 m and A6 about 10 m.", ["runnerDisplacementM", "markerDisplacementM"]))
    assert check(SPACE, exp) == []


def test_invented_number_is_rejected():
    exp = _explanation(("A6 was dragged 20 m out of position.", ["markerDisplacementM"]))
    problems = check(SPACE, exp)
    assert len(problems) == 1 and "20" in problems[0]


def test_derived_number_is_rejected():
    # 11.1 - 5.0 = 6.1 is true, but it is not a measured value, so it must not be quoted.
    exp = _explanation(("A6 ended 6.1 m further from the zone.", ["markerDistanceToTargetEndM"]))
    assert any("6.1" in p for p in check(SPACE, exp))


def test_claim_without_evidence_is_rejected():
    exp = _explanation(("H10 is the best runner in the league.", []))
    assert any("cites no evidence" in p for p in check(SPACE, exp))


def test_unknown_field_is_rejected():
    exp = _explanation(("H10 sprinted at top speed.", ["sprintSpeed"]))
    assert any("sprintSpeed" in p for p in check(SPACE, exp))


def test_player_ids_are_not_treated_as_numbers():
    exp = _explanation(
        ("H8 and H6 played a one-two that took A10 and A11 out of play.", ["pattern", "bypassedIds"]),
        ("It took out 2 opponents, 3.6 s before the assist.", ["opponentsBypassed", "secondsBeforeFinalPass"]),
        headline="The chance began with H8 and H6's one-two",
    )
    assert check(ORIGIN, exp) == []
