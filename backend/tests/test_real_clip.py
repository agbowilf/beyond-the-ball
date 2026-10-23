"""The committed real-data clip: its insights must be exactly what the detectors produce today."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.run_analysis import analyse  # noqa: E402

CLIP = ROOT / "scenarios" / "real" / "metrica_g2_shot_12.json"


def test_committed_insights_match_the_detectors():
    clip = json.loads(CLIP.read_text())
    committed = json.loads(CLIP.with_name(CLIP.stem + ".insights.json").read_text())
    assert analyse(clip) == committed


def test_real_clip_finds_the_decoy_run_and_credits_its_source():
    clip = json.loads(CLIP.read_text())
    [space] = [i for i in analyse(clip) if i["type"] == "SPACE_CREATOR"]
    assert (space["playerId"], space["markerId"]) == ("H10", "A3")
    assert space["evidence"]["runnerTouches"] == 0
    assert "Metrica" in clip["source"]["dataset"]
