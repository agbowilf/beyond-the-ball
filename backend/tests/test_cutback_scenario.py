"""Scenario 02 (cut-back) exercises what the demo does not: a single line-breaking pass, a cut-back assist and a
deep-dropping back line. Both detectors must find the designed pattern, and nothing else."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.run_analysis import analyse  # noqa: E402


def _scenario():
    spec = importlib.util.spec_from_file_location("gen_cutback", ROOT / "scenarios" / "generate_cutback.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build()


def test_finds_the_near_post_run_that_emptied_the_cut_back_zone():
    insights = analyse(_scenario())
    [space] = [i for i in insights if i["type"] == "SPACE_CREATOR"]
    assert (space["playerId"], space["markerId"]) == ("H9", "A5")
    ev = space["evidence"]
    assert ev["runnerTouches"] == 0
    assert ev["backLineDropM"] >= 5
    assert ev["freeSpaceRatio"] >= 1.5


def test_origin_is_a_single_line_breaking_pass_ending_in_a_cut_back():
    scenario = _scenario()
    [origin] = [i for i in analyse(scenario) if i["type"] == "SEQUENCE_ORIGIN"]
    assert origin["pattern"] == "LINE_BREAKING_PASS"
    assert (origin["playerId"], origin["partnerId"]) == ("H6", "H8")
    assert origin["evidence"]["opponentsBypassed"] >= 2
    assist = max((e for e in scenario["events"] if e["type"] == "PASS"), key=lambda e: e["t"])
    assert assist["end"]["x"] < assist["start"]["x"] - 5  # a genuine cut-back
