"""Detectors must follow the football, not the pitch side or team labels of one scenario.

Each test transforms the decoy-run scenario into a geometrically equivalent move and checks every
detector finds the same insight, transformed the same way.
"""
import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.run_analysis import analyse  # noqa: E402

LENGTH, WIDTH = 105, 68


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen", ROOT / "scenarios" / "generate_decoy_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _transform(scenario, point, ident=lambda pid: pid, team=lambda t: t):
    """Apply a point mapping and an id/team relabelling to every frame and event."""
    out = copy.deepcopy(scenario)

    def move(obj):
        obj["x"], obj["y"] = (round(v, 2) for v in point(obj["x"], obj["y"]))

    for f in out["frames"]:
        move(f["ball"])
        for p in f["players"]:
            move(p)
            p["id"], p["team"] = ident(p["id"]), team(p["team"])
    for e in out["events"]:
        e["team"] = team(e["team"])
        for key in ("playerId", "targetPlayerId"):
            if key in e:
                e[key] = ident(e[key])
        for key in ("start", "end", "location"):
            if key in e:
                move(e[key])
    return out


def _swap_id(pid):
    return ("A" if pid[0] == "H" else "H") + pid[1:]


def _swap_team(t):
    return "AWAY" if t == "HOME" else "HOME"


def _relabel_insight(insight):
    """What an insight should look like after the HOME/AWAY swap."""
    out = copy.deepcopy(insight)
    out["team"] = _swap_team(out["team"])
    for key in ("playerId", "markerId", "partnerId"):
        if key in out:
            out[key] = _swap_id(out[key])
    if "bypassedIds" in out:
        out["bypassedIds"] = [_swap_id(pid) for pid in out["bypassedIds"]]
    return out


def _swap_sides(insight):
    """Mirroring across the width swaps the attackers' left and right."""
    out = copy.deepcopy(insight)
    if "targetZone" in out:
        out["targetZone"] = (out["targetZone"].replace("left", "\0").replace("right", "left").replace("\0", "right"))
    return out


def test_same_move_down_the_other_flank():
    scenario = _load_generator().build()
    mirrored = _transform(scenario, lambda x, y: (x, WIDTH - y))
    assert analyse(mirrored) == [_swap_sides(i) for i in analyse(scenario)]


def test_side_swap_relabels_off_centre_zones():
    assert _swap_sides({"targetZone": "left half-space, penalty area"})["targetZone"] == "right half-space, penalty area"


def test_same_move_by_the_away_team():
    scenario = _load_generator().build()
    # Rotate the pitch 180 degrees and swap the team labels: AWAY now makes the move, attacking -x.
    rotated = _transform(scenario, lambda x, y: (LENGTH - x, WIDTH - y), _swap_id, _swap_team)
    expected = [_relabel_insight(i) for i in analyse(scenario)]
    assert analyse(rotated) == expected
    assert {i["type"] for i in expected} == {"SPACE_CREATOR", "SEQUENCE_ORIGIN"}
