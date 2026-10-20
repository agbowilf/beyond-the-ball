"""Space Creator detector (v0.1). See docs/detection-rules.md.

Reads only frames and events. Never reads scenario labels.
"""
import math

SHOT_WINDOW_S = 5.0
LOOKBACK_S = 5.0
MIN_RUNNER_DISP_M = 6.0
MIN_MARKER_DISP_M = 4.0
MIN_FOLLOW_COSINE = 0.5
MIN_MARKER_PULL_M = 3.0


def _clip(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _frame_at(frames, t):
    return min(frames, key=lambda f: abs(f["t"] - t))


def _pos(frame, pid):
    for p in frame["players"]:
        if p["id"] == pid:
            return (p["x"], p["y"])
    raise KeyError(pid)


def _outfield(frame, team):
    # Goalkeepers are shirt number 1 (H1 / A1) and are excluded from marker checks.
    return [p for p in frame["players"] if p["team"] == team and p["id"][1:] != "1"]


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _cos(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu == 0 or nv == 0:
        return 0.0
    return (u[0] * v[0] + u[1] * v[1]) / (nu * nv)


LENGTH, WIDTH = 105.0, 68.0
# Lane edges across the pitch (penalty-area and goal-area edges), low y to high y.
LANE_EDGES = (13.84, 24.84, 43.16, 54.16)
LANES_HIGH_Y_IS_LEFT = ("right wing", "right half-space", "central lane", "left half-space", "left wing")


def target_zone(point, team):
    """Lane and area of the pitch for `point`, from `team`'s attacking point of view. HOME attacks +x."""
    x, y = point
    if team != "HOME":  # AWAY attacks -x: rotate so the same rules apply
        x, y = LENGTH - x, WIDTH - y
    lane = LANES_HIGH_Y_IS_LEFT[sum(y > edge for edge in LANE_EDGES)]
    if x >= LENGTH - 16.5 and LANE_EDGES[0] <= y <= LANE_EDGES[-1]:
        area = "penalty area"
    elif x >= LENGTH * 2 / 3:
        area = "attacking third"
    elif x >= LENGTH / 3:
        area = "middle third"
    else:
        area = "defensive third"
    return f"{lane}, {area}"


def _touches(events, player_id, t0, t1):
    return sum(1 for e in events
               if e["type"] in ("PASS", "RECEIVE", "SHOT") and e["playerId"] == player_id and t0 <= e["t"] <= t1)


def detect_space_creators(scenario):
    frames, events = scenario["frames"], scenario["events"]
    insights = []
    passes = [e for e in events if e["type"] == "PASS"]
    shots = [e for e in events if e["type"] == "SHOT"]

    for ps in passes:
        shot = next((s for s in shots if s["team"] == ps["team"] and 0 <= s["t"] - ps["t"] <= SHOT_WINDOW_S), None)
        if shot is None:
            continue
        team = ps["team"]
        opp = "AWAY" if team == "HOME" else "HOME"
        target = (ps["end"]["x"], ps["end"]["y"])
        f0 = _frame_at(frames, ps["t"] - LOOKBACK_S)
        f1 = _frame_at(frames, ps["t"])

        for p in f0["players"]:
            if p["team"] != team or p["id"] in (ps["playerId"], ps["targetPlayerId"]):
                continue
            r0, r1 = (p["x"], p["y"]), _pos(f1, p["id"])
            r_vec = (r1[0] - r0[0], r1[1] - r0[1])
            r_disp = math.hypot(*r_vec)
            if r_disp < MIN_RUNNER_DISP_M:
                continue

            defenders0 = _outfield(f0, opp)
            marker = min(defenders0, key=lambda d: _dist((d["x"], d["y"]), r0))
            m0, m1 = (marker["x"], marker["y"]), _pos(f1, marker["id"])
            m_vec = (m1[0] - m0[0], m1[1] - m0[1])
            m_disp = math.hypot(*m_vec)
            cosine = _cos(r_vec, m_vec)
            m_d0, m_d1 = _dist(m0, target), _dist(m1, target)
            pull = m_d1 - m_d0

            if m_disp < MIN_MARKER_DISP_M or cosine < MIN_FOLLOW_COSINE or pull < MIN_MARKER_PULL_M:
                continue

            near0 = min(_dist((d["x"], d["y"]), target) for d in defenders0)
            near1 = min(_dist((d["x"], d["y"]), target) for d in _outfield(f1, opp))
            parts = {"pull": _clip(pull / 8), "follow": _clip(cosine), "free": _clip((near1 - near0) / 6)}
            confidence = 0.4 * parts["pull"] + 0.3 * parts["follow"] + 0.3 * parts["free"]
            free0, free1 = math.pi * near0**2, math.pi * near1**2

            insights.append({
                "type": "SPACE_CREATOR",
                "t": ps["t"],
                "team": team,
                "playerId": p["id"],
                "markerId": marker["id"],
                "targetZone": target_zone(target, team),
                "confidence": round(confidence, 2),
                "confidenceParts": {k: round(v, 2) for k, v in parts.items()},
                "evidence": {
                    "runnerDisplacementM": round(r_disp, 1),
                    "markerDisplacementM": round(m_disp, 1),
                    "markerFollowCosine": round(cosine, 2),
                    "markerDistanceToTargetStartM": round(m_d0, 1),
                    "markerDistanceToTargetEndM": round(m_d1, 1),
                    "nearestDefenderToTargetStartM": round(near0, 1),
                    "nearestDefenderToTargetEndM": round(near1, 1),
                    "shotSecondsAfterPass": round(shot["t"] - ps["t"], 1),
                    "runnerTouches": _touches(events, p["id"], ps["t"] - LOOKBACK_S, shot["t"]),
                    "freeSpaceStartM2": round(free0),
                    "freeSpaceEndM2": round(free1),
                    "freeSpaceGainM2": round(free1 - free0),
                    "freeSpaceRatio": round(free1 / free0, 1) if free0 else None,
                    "markerPullM": round(pull, 1),
                },
            })
    return sorted(insights, key=lambda i: -i["confidence"])
