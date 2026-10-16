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
            confidence = (0.4 * _clip(pull / 8) + 0.3 * _clip(cosine) + 0.3 * _clip((near1 - near0) / 6))

            insights.append({
                "type": "SPACE_CREATOR",
                "t": ps["t"],
                "team": team,
                "playerId": p["id"],
                "markerId": marker["id"],
                "confidence": round(confidence, 2),
                "evidence": {
                    "runnerDisplacementM": round(r_disp, 1),
                    "markerDisplacementM": round(m_disp, 1),
                    "markerFollowCosine": round(cosine, 2),
                    "markerDistanceToTargetStartM": round(m_d0, 1),
                    "markerDistanceToTargetEndM": round(m_d1, 1),
                    "nearestDefenderToTargetStartM": round(near0, 1),
                    "nearestDefenderToTargetEndM": round(near1, 1),
                    "shotSecondsAfterPass": round(shot["t"] - ps["t"], 1),
                },
            })
    return sorted(insights, key=lambda i: -i["confidence"])
