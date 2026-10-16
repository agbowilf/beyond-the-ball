"""Plausibility checks on the synthetic scenarios themselves, independent of any detector."""
import importlib.util
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_SPEED_MS = 9.0  # well above a typical top sprint of ~8.5 m/s, so only glitches fail


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen", ROOT / "scenarios" / "generate_decoy_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_attacker_offside_before_final_pass():
    scenario = _load_generator().build()
    final_pass = max(e["t"] for e in scenario["events"] if e["type"] == "PASS")
    for f in scenario["frames"]:
        if f["t"] > final_pass:
            break
        # Second-last opponent, goalkeeper included. HOME attacks +x.
        line = sorted((p["x"] for p in f["players"] if p["team"] == "AWAY"), reverse=True)[1]
        offside = [p["id"] for p in f["players"]
                   if p["team"] == "HOME" and p["x"] > line and p["x"] > f["ball"]["x"]]
        assert offside == [], f"offside at t={f['t']}: {offside}"


def test_player_speeds_are_humanly_possible():
    scenario = _load_generator().build()
    frames, hz = scenario["frames"], scenario["sampleRateHz"]
    for a, b in zip(frames, frames[1:]):
        for pa, pb in zip(a["players"], b["players"]):
            speed = math.hypot(pb["x"] - pa["x"], pb["y"] - pa["y"]) * hz
            assert speed <= MAX_SPEED_MS, f"{pa['id']} at {speed:.1f} m/s near t={a['t']}"


def test_every_player_moves():
    scenario = _load_generator().build()
    first, last = scenario["frames"][0]["players"], scenario["frames"][-1]["players"]
    for p, q in zip(first, last):
        assert math.hypot(q["x"] - p["x"], q["y"] - p["y"]) >= 3.0, f"{p['id']} barely moves"
