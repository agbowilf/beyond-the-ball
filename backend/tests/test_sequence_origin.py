import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.analysis.sequence_origin import detect_sequence_origins  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen", ROOT / "scenarios" / "generate_decoy_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_detects_one_two_as_origin():
    insights = detect_sequence_origins(_load_generator().build())
    assert len(insights) == 1
    top = insights[0]
    assert top["type"] == "SEQUENCE_ORIGIN"
    assert top["pattern"] == "ONE_TWO"
    assert (top["playerId"], top["partnerId"]) == ("H8", "H6")
    assert top["bypassedIds"] == ["A10", "A11"]
    assert top["evidence"]["opponentsBypassed"] == 2


def test_confidence_is_the_weighted_parts():
    top = detect_sequence_origins(_load_generator().build())[0]
    p = top["confidenceParts"]
    assert abs(top["confidence"] - (0.6 * p["lines"] + 0.4 * p["progress"])) <= 0.01


def test_origin_comes_before_the_assist():
    scenario = _load_generator().build()
    final_pass = max(e["t"] for e in scenario["events"] if e["type"] == "PASS")
    top = detect_sequence_origins(scenario)[0]
    assert top["t"] < final_pass
    assert top["evidence"]["secondsBeforeFinalPass"] > 0


def test_single_line_breaking_pass_without_one_two():
    scenario = copy.deepcopy(_load_generator().build())
    # Drop the one-two: the chain becomes H6 -> H8 -> H11, and only the assist breaks a line.
    one_two = next(e["t"] for e in scenario["events"] if e["type"] == "PASS" and e["playerId"] == "H8")
    scenario["events"] = [e for e in scenario["events"] if not one_two <= e["t"] < one_two + 1.6]
    top = detect_sequence_origins(scenario)[0]
    assert top["pattern"] == "LINE_BREAKING_PASS"
    assert (top["playerId"], top["partnerId"]) == ("H8", "H11")


def test_no_origin_when_no_opponent_is_bypassed():
    scenario = copy.deepcopy(_load_generator().build())
    # Every opponent stays goal-side of the ball throughout, so no pass breaks a line.
    for f in scenario["frames"]:
        for p in f["players"]:
            if p["team"] == "AWAY":
                p["x"] = 104.0
    assert detect_sequence_origins(scenario) == []


def test_no_origin_without_shot():
    scenario = copy.deepcopy(_load_generator().build())
    scenario["events"] = [e for e in scenario["events"] if e["type"] not in ("SHOT", "GOAL")]
    assert detect_sequence_origins(scenario) == []


def test_origin_never_comes_before_a_turnover():
    scenario = copy.deepcopy(_load_generator().build())
    one_two = next(e["t"] for e in scenario["events"] if e["type"] == "PASS" and e["playerId"] == "H8")
    # The defenders win the ball just after the lay-off and lose it straight back: the one-two no longer counts.
    scenario["events"] += [{"t": one_two + 0.2, "type": "POSSESSION_CHANGE", "team": "AWAY"},
                           {"t": one_two + 0.3, "type": "POSSESSION_CHANGE", "team": "HOME"}]
    scenario["events"].sort(key=lambda e: e["t"])
    for origin in detect_sequence_origins(scenario):
        assert origin["t"] > one_two + 0.2


def test_a_cut_back_assist_does_not_cancel_the_origin():
    scenario = copy.deepcopy(_load_generator().build())
    # Turn the assist into a cut-back: it now travels 8 m backwards to the receiver.
    assist = max((e for e in scenario["events"] if e["type"] == "PASS"), key=lambda e: e["t"])
    assist["end"] = {"x": assist["start"]["x"] - 8.0, "y": assist["end"]["y"]}
    top = detect_sequence_origins(scenario)
    assert top and (top[0]["playerId"], top[0]["partnerId"]) == ("H8", "H6")


def test_a_backward_pass_before_the_assist_still_breaks_the_chain():
    scenario = copy.deepcopy(_load_generator().build())
    passes = sorted((e for e in scenario["events"] if e["type"] == "PASS"), key=lambda e: e["t"])
    # The pass between the one-two and the assist goes 8 m backwards: the attack did not keep progressing.
    one_two_return = passes[-2]
    one_two_return["end"] = {"x": one_two_return["start"]["x"] - 8.0, "y": one_two_return["end"]["y"]}
    origins = detect_sequence_origins(scenario)
    assert origins and all(origin["t"] > one_two_return["t"] for origin in origins)
