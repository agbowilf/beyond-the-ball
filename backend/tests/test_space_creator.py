import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.analysis.space_creator import detect_space_creators  # noqa: E402


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
