import copy
import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.analysis.space_creator import detect_space_creators, target_zone  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen", ROOT / "scenarios" / "generate_decoy_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_detects_decoy_runner():
    scenario = _load_generator().build()
    insights = detect_space_creators(scenario)
    assert len(insights) == 1
    top = insights[0]
    assert top["type"] == "SPACE_CREATOR"
    assert top["playerId"] == "H10"
    assert top["markerId"] == "A6"
    # A realistic marker follows only a few metres before handing the runner on, so confidence is moderate.
    assert top["confidence"] >= 0.6
    ev = top["evidence"]
    assert ev["markerDistanceToTargetEndM"] - ev["markerDistanceToTargetStartM"] >= 3
    assert ev["nearestDefenderToTargetEndM"] > ev["nearestDefenderToTargetStartM"]


def test_no_insight_when_marker_does_not_follow():
    scenario = _load_generator().build()
    scenario = copy.deepcopy(scenario)
    # Freeze A6 at its starting position in every frame: nobody tracks the run.
    start = next(p for p in scenario["frames"][0]["players"] if p["id"] == "A6")
    for f in scenario["frames"]:
        for p in f["players"]:
            if p["id"] == "A6":
                p["x"], p["y"] = start["x"], start["y"]
    assert detect_space_creators(scenario) == []


def test_no_insight_without_shot():
    scenario = copy.deepcopy(_load_generator().build())
    scenario["events"] = [e for e in scenario["events"] if e["type"] not in ("SHOT", "GOAL")]
    assert detect_space_creators(scenario) == []


def test_reports_touches_free_space_and_zone():
    top = detect_space_creators(_load_generator().build())[0]
    ev = top["evidence"]
    assert top["targetZone"] == "central lane, penalty area"
    assert ev["runnerTouches"] == 0  # H10 never plays, receives or shoots during the move
    assert ev["freeSpaceEndM2"] > ev["freeSpaceStartM2"]
    assert abs(ev["freeSpaceGainM2"] - (ev["freeSpaceEndM2"] - ev["freeSpaceStartM2"])) <= 1
    assert abs(ev["freeSpaceEndM2"] - math.pi * ev["nearestDefenderToTargetEndM"] ** 2) <= 0.02 * ev["freeSpaceEndM2"]


def test_reports_space_ratio_and_marker_pull():
    ev = detect_space_creators(_load_generator().build())[0]["evidence"]
    assert abs(ev["freeSpaceRatio"] - ev["freeSpaceEndM2"] / ev["freeSpaceStartM2"]) <= 0.1
    assert abs(ev["markerPullM"] - (ev["markerDistanceToTargetEndM"] - ev["markerDistanceToTargetStartM"])) <= 0.1


def test_a_runner_touch_is_counted():
    scenario = copy.deepcopy(_load_generator().build())
    scenario["events"].append({"t": 7.0, "type": "RECEIVE", "team": "HOME", "playerId": "H10",
                               "location": {"x": 80.0, "y": 48.0}})
    assert detect_space_creators(scenario)[0]["evidence"]["runnerTouches"] == 1


def test_confidence_is_the_weighted_parts():
    top = detect_space_creators(_load_generator().build())[0]
    p = top["confidenceParts"]
    assert abs(top["confidence"] - (0.4 * p["pull"] + 0.3 * p["follow"] + 0.3 * p["free"])) <= 0.01


def test_target_zone_lanes_and_areas():
    assert target_zone((95, 60), "HOME") == "left wing, attacking third"
    assert target_zone((95, 20), "HOME") == "right half-space, penalty area"
    assert target_zone((50, 34), "HOME") == "central lane, middle third"
    assert target_zone((20, 34), "HOME") == "central lane, defensive third"
    # AWAY attacks -x, so its left is low y.
    assert target_zone((10, 20), "AWAY") == "left half-space, penalty area"


def test_no_insight_when_the_space_does_not_grow():
    scenario = copy.deepcopy(_load_generator().build())
    # Park a covering defender on the receiving spot for the whole clip: A6 is still pulled, but no space opens.
    target = next(e for e in scenario["events"] if e["type"] == "PASS" and e["playerId"] == "H8"
                  and e["targetPlayerId"] == "H11")["end"]
    for f in scenario["frames"]:
        for p in f["players"]:
            if p["id"] == "A4":
                p["x"], p["y"] = target["x"] + 1.0, target["y"]
    assert detect_space_creators(scenario) == []


def test_no_credit_for_dragging_a_defender_who_was_not_covering_the_spot():
    scenario = copy.deepcopy(_load_generator().build())
    # A second defender sits much closer to the receiving spot at the start of the run, then steps away,
    # so A6 was not the one guarding it.
    t_pass = next(e["t"] for e in scenario["events"] if e["type"] == "PASS" and e["targetPlayerId"] == "H11")
    target = next(e["end"] for e in scenario["events"] if e["type"] == "PASS" and e["targetPlayerId"] == "H11")
    for f in scenario["frames"]:
        for p in f["players"]:
            if p["id"] == "A4":
                near = f["t"] <= t_pass - 5 + 0.3
                p["x"], p["y"] = (target["x"] - 1.0, target["y"]) if near else (60.0, 10.0)
    assert detect_space_creators(scenario) == []
