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


def test_origin_comes_before_the_assist():
    scenario = _load_generator().build()
    final_pass = max(e["t"] for e in scenario["events"] if e["type"] == "PASS")
    top = detect_sequence_origins(scenario)[0]
    assert top["t"] < final_pass
    assert top["evidence"]["secondsBeforeFinalPass"] > 0


def test_single_line_breaking_pass_without_one_two():
    scenario = copy.deepcopy(_load_generator().build())
    # Drop the one-two: the chain becomes H6 -> H8 -> H11, and only the assist breaks a line.
    scenario["events"] = [e for e in scenario["events"] if not 2.0 < e["t"] < 4.0]
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
