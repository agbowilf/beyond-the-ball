"""Sequence Origin detector (v0.1). See docs/detection-rules.md.

Reads only frames and events. Never reads scenario labels.
"""
MAX_LOOKBACK_S = 15.0
MIN_BYPASSED = 2
MAX_BACKWARD_M = 2.0
ONE_TWO_MAX_S = 2.0


def _clip(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _frame_at(frames, t):
    return min(frames, key=lambda f: abs(f["t"] - t))


def _attack_sign(team):
    # HOME always attacks +x (docs/data-model.md).
    return 1 if team == "HOME" else -1


def _chain(events, shot):
    """Completed passes that moved the ball, holder to holder, to the shooter."""
    passes = [e for e in events
              if e["type"] == "PASS" and e["team"] == shot["team"] and e.get("outcome") == "COMPLETE"]
    chain, holder, before = [], shot["playerId"], shot["t"]
    while True:
        prev = [p for p in passes
                if p["targetPlayerId"] == holder and p["t"] < before and shot["t"] - p["t"] <= MAX_LOOKBACK_S]
        if not prev:
            return chain
        p = max(prev, key=lambda e: e["t"])
        chain.insert(0, p)
        holder, before = p["playerId"], p["t"]


def _receive_t(events, ps):
    rec = [e for e in events
           if e["type"] == "RECEIVE" and e["playerId"] == ps["targetPlayerId"] and e["t"] > ps["t"]]
    return min(e["t"] for e in rec) if rec else None


def _bypassed(frames, ps, t_recv, sign):
    """Opposing outfield players goal-side of the ball when it was played but not when received."""
    f0, f1 = _frame_at(frames, ps["t"]), _frame_at(frames, t_recv)
    opp = "AWAY" if ps["team"] == "HOME" else "HOME"

    def goal_side(f):
        return {p["id"] for p in f["players"]
                if p["team"] == opp and p["id"][1:] != "1" and sign * (p["x"] - f["ball"]["x"]) > 0}

    return sorted(goal_side(f0) - goal_side(f1), key=lambda pid: int(pid[1:]))


def detect_sequence_origins(scenario):
    frames, events = scenario["frames"], scenario["events"]
    insights = []

    for shot in (e for e in events if e["type"] == "SHOT"):
        sign = _attack_sign(shot["team"])
        chain = _chain(events, shot)
        for i, ps in enumerate(chain):
            t_recv = _receive_t(events, ps)
            if t_recv is None:
                continue
            bypassed = _bypassed(frames, ps, t_recv, sign)
            forward_after = all(sign * (p["end"]["x"] - p["start"]["x"]) >= -MAX_BACKWARD_M for p in chain[i:])
            if len(bypassed) < MIN_BYPASSED or not forward_after:
                continue

            origin, pattern, partner = ps, "LINE_BREAKING_PASS", ps["targetPlayerId"]
            prev = chain[i - 1] if i > 0 else None
            if (prev and prev["playerId"] == ps["targetPlayerId"] and prev["targetPlayerId"] == ps["playerId"]
                    and ps["t"] - prev["t"] <= ONE_TWO_MAX_S):
                origin, pattern, partner = prev, "ONE_TWO", ps["playerId"]

            progression = sign * (shot["location"]["x"] - origin["start"]["x"])
            parts = {"lines": _clip(len(bypassed) / 3), "progress": _clip(progression / 25)}
            confidence = 0.6 * parts["lines"] + 0.4 * parts["progress"]
            insights.append({
                "type": "SEQUENCE_ORIGIN",
                "t": origin["t"],
                "team": shot["team"],
                "playerId": origin["playerId"],
                "partnerId": partner,
                "pattern": pattern,
                "bypassedIds": bypassed,
                "confidence": round(confidence, 2),
                "confidenceParts": {k: round(v, 2) for k, v in parts.items()},
                "evidence": {
                    "opponentsBypassed": len(bypassed),
                    "lineBreakingPassT": ps["t"],
                    "passesToShot": len(chain) - chain.index(origin),
                    "progressionM": round(progression, 1),
                    "secondsBeforeFinalPass": round(chain[-1]["t"] - origin["t"], 1),
                    "secondsBeforeShot": round(shot["t"] - origin["t"], 1),
                },
            })
            break
    return insights
