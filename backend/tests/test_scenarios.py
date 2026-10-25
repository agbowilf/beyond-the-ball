"""Plausibility checks on the synthetic scenarios themselves, independent of any detector."""
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAX_SPEED_MS = 9.0  # well above a typical top sprint of ~8.5 m/s, so only glitches fail


GENERATORS = sorted((ROOT / "scenarios").glob("generate_*.py"))


def _build(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build()


# Every check runs on every scenario generator, so a new scenario is held to the same standard.
every_scenario = pytest.mark.parametrize("generator", GENERATORS, ids=lambda p: p.stem)


def test_there_is_more_than_one_scenario():
    assert len(GENERATORS) >= 2


@every_scenario
def test_no_attacker_offside_before_final_pass(generator):
    scenario = _build(generator)
    final_pass = max(e["t"] for e in scenario["events"] if e["type"] == "PASS")
    for f in scenario["frames"]:
        if f["t"] > final_pass:
            break
        # Second-last opponent, goalkeeper included. HOME attacks +x.
        line = sorted((p["x"] for p in f["players"] if p["team"] == "AWAY"), reverse=True)[1]
        offside = [p["id"] for p in f["players"]
                   if p["team"] == "HOME" and p["x"] > line and p["x"] > f["ball"]["x"]]
        assert offside == [], f"offside at t={f['t']}: {offside}"


@every_scenario
def test_player_speeds_are_humanly_possible(generator):
    scenario = _build(generator)
    frames, hz = scenario["frames"], scenario["sampleRateHz"]
    for a, b in zip(frames, frames[1:]):
        for pa, pb in zip(a["players"], b["players"]):
            speed = math.hypot(pb["x"] - pa["x"], pb["y"] - pa["y"]) * hz
            assert speed <= MAX_SPEED_MS, f"{pa['id']} at {speed:.1f} m/s near t={a['t']}"


@every_scenario
def test_every_player_moves(generator):
    scenario = _build(generator)
    first, last = scenario["frames"][0]["players"], scenario["frames"][-1]["players"]
    for p, q in zip(first, last):
        assert math.hypot(q["x"] - p["x"], q["y"] - p["y"]) >= 3.0, f"{p['id']} barely moves"


@every_scenario
def test_goal_shot_beats_the_keeper(generator):
    scenario = _build(generator)
    shot = next(e for e in scenario["events"] if e["type"] == "SHOT" and e["outcome"] == "GOAL")
    goal = next(e for e in scenario["events"] if e["type"] == "GOAL")
    for f in scenario["frames"]:
        if shot["t"] < f["t"] <= goal["t"]:
            keeper = next(p for p in f["players"] if p["id"] == "A1")
            gap = math.hypot(f["ball"]["x"] - keeper["x"], f["ball"]["y"] - keeper["y"])
            assert gap > 1.5, f"ball passes through the keeper at t={f['t']} ({gap:.1f} m)"
    end = scenario["frames"][-1]["ball"]
    assert end["x"] >= 105 and 30.34 < end["y"] < 37.66, "ball must finish inside the goal"


@every_scenario
def test_passes_do_not_go_through_opponents(generator):
    scenario = _build(generator)
    events = scenario["events"]
    passes = [(e["t"], next(r["t"] for r in events if r["type"] == "RECEIVE" and r["t"] > e["t"]))
              for e in events if e["type"] == "PASS"]
    for f in scenario["frames"]:
        if any(t0 < f["t"] < t1 for t0, t1 in passes):
            for p in f["players"]:
                if p["team"] == "AWAY":
                    gap = math.hypot(f["ball"]["x"] - p["x"], f["ball"]["y"] - p["y"])
                    assert gap > 1.5, f"pass in flight runs through {p['id']} at t={f['t']} ({gap:.1f} m)"
