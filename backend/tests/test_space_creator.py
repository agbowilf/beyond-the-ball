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
    assert top["confidence"] >= 0.8
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


def test_a_runner_touch_is_counted():
    scenario = copy.deepcopy(_load_generator().build())
    scenario["events"].append({"t": 3.0, "type": "RECEIVE", "team": "HOME", "playerId": "H10",
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
