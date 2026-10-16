"""Generate scenario 01: a decoy run that opens space for a goal.

This script only emits raw tracking frames and events. It contains no detection logic and writes no
insight labels; the analysis engine has to find the pattern on its own.

Pitch: 105 x 68 m. HOME attacks toward +x.

Story: HOME work the ball from H6 to H8, who carries it at a 4-4-2 AWAY block. H10, in the pocket in
front of centre-back A6, checks toward the ball and then spins out into the right channel. A6 follows a
beat late, which empties the gap between the centre-backs. H9 holds A5 in place and H11 makes a blindside
run from the left into that gap, timed to stay onside, and scores. Every attacker is level with or behind
the AWAY back line until the final pass.
"""
import json
import math
import random
import sys
from pathlib import Path

HZ = 5
DURATION = 10.0  # seconds
SEED = 7
NOISE_M = 0.06
SWAY_M = 0.25  # slow idle drift so nobody stands perfectly still

# Keyframes: player -> list of (t, x, y). Smooth (Catmull-Rom) interpolation through keyframes.
HOME = {
    "H1": [(0, 40, 34), (6, 43, 34), (10, 46, 34)],
    # Left back overlaps outside H11 to give A2 a second problem
    "H2": [(0, 66, 8), (1.2, 71, 7), (2.4, 75.5, 6), (3.6, 79.5, 5.5), (4.8, 82, 5.5), (6, 83, 6), (8, 84.5, 7),
           (10, 86, 9)],
    "H3": [(0, 63, 60), (3, 65, 61), (6, 68, 61), (10, 72, 61)],       # right back pushes on
    "H4": [(0, 50, 26), (6, 54, 27), (10, 58, 28)],
    "H5": [(0, 50, 42), (6, 54, 41), (10, 58, 40)],
    "H6": [(0, 58, 30), (0.6, 58.3, 30.2), (3, 61, 31), (6, 63, 31), (10, 67, 32)],  # passes to H8 at 0.6
    "H7": [(0, 80, 63), (3, 81.5, 63), (6, 82.5, 62.5), (8, 86.5, 60.5), (10, 89.5, 60)],  # holds the width
    # Carries from t=1.4 and plays the through ball at t=6
    "H8": [(0, 61.5, 40.5), (1.4, 64, 36), (3, 66, 35.5), (4.5, 68, 35.5), (6, 70, 35), (7, 71, 35), (10, 76, 36)],
    # Striker holds A5 from its outside shoulder, staying a stride onside, then attacks the far post after the pass
    "H9": [(0, 83, 23.5), (2, 83.5, 22.5), (4, 84, 21.5), (6, 85, 21.5), (7.4, 89.5, 25.5), (9, 93.5, 28.5), (10, 94.5, 29.5)],
    # Decoy runner: drifts in the pocket, checks toward the ball, then spins into the right channel
    "H10": [(0, 79, 42), (1, 80, 43.5), (2, 78.5, 45), (3, 80, 48), (4, 82.5, 52), (5, 84, 55.5),
            (6, 84.8, 57), (8, 88, 55.5), (10, 91, 53)],
    # Left winger: checks short to pull A2 out, then spins in behind A2 into the gap A6 leaves,
    # onside at the pass, receives at t=7.4
    "H11": [(0, 78, 13), (1.2, 76.5, 11.5), (2.4, 77.3, 12), (3.4, 79.8, 17), (4.6, 82.4, 24.5), (6, 85, 32.5),
            (7.4, 89, 41), (8.2, 90, 41.5), (10, 92, 42)],
}
AWAY = {
    # Keeper comes out to narrow the near-post angle, then dives across too late for the far corner
    "A1": [(0, 100, 34), (6, 99.5, 35), (7.4, 101, 37.5), (8.2, 102.3, 36.8), (8.8, 103.3, 34.5),
           (10, 103.4, 34.3)],
    # Back four: holds about 84 m, edges back as H8 advances, then turns and retreats after the pass.
    # Full-back follows H11's check, hesitates over H2's overlap, then chases H11's spin a step behind
    "A2": [(0, 84.5, 12.5), (1.2, 82, 12.5), (2.4, 81, 11.5), (3.4, 81.6, 14), (4.6, 81.8, 21.5),
           (5.3, 82.7, 26.3), (6, 84, 30), (7.4, 87.5, 38), (8.2, 89, 39.6), (10, 90.5, 40)],
    # Held by H9, then tracks H9's far-post run
    "A5": [(0, 84, 27), (2, 84.4, 26), (4, 85.4, 24.5), (6, 86.2, 24), (7.4, 88, 28), (8.2, 90, 29.5),
           (10, 92.5, 32)],
    # Right centre-back: reacts to H10's check, follows the run a beat late, then lets H10 go wide
    "A6": [(0, 84, 42), (1, 84, 42.5), (2, 83, 44), (3, 83.5, 46.5), (4, 84.5, 49), (5, 85.3, 50.5),
           (6, 86, 51.5), (7.4, 88, 50), (10, 89.5, 49)],
    "A3": [(0, 84, 58), (3, 84.5, 60), (6, 85, 61.5), (8, 89, 59), (10, 92, 57)],  # stays wide with H7
    # Midfield four steps up and narrows on the ball, then sprints back. A4 shades toward H2's overlap
    "A4": [(0, 74, 19), (3, 73.5, 20.5), (6, 74.5, 19), (8, 78, 22), (10, 82, 26)],
    "A8": [(0, 74, 30), (2, 72.5, 31.5), (4, 72, 32.5), (6, 73, 32.5), (8, 77, 33), (10, 81, 33)],
    "A10": [(0, 75, 41), (1.5, 73, 39.5), (3, 71.5, 38), (4.5, 72, 37), (6, 72.5, 36.5), (8, 76, 37),
            (10, 80, 38)],                                              # presses H8
    "A7": [(0, 74, 52), (3, 74, 50), (6, 75, 48.5), (8, 79, 47), (10, 83, 46)],
    # Front two: A9 presses H6, A11 screens H8's side, then both drop
    "A9": [(0, 62.5, 26.5), (0.6, 60.5, 28.5), (2, 62.5, 29.5), (6, 66, 30), (10, 70, 31)],
    "A11": [(0, 66, 41), (2, 66.5, 41.5), (6, 67, 41), (10, 70.5, 40)],
}

PASS_T, RECEIVE_T, SHOT_T, GOAL_T = 6.0, 7.4, 8.2, 8.9
TARGET = (89.0, 41.0)
GOAL_POINT = (106.0, 31.2)  # low, across the keeper, inside the far post (y=30.34)

# Ball possession plan: (passer, pass t, receiver, receive t, end point or None for the receiver's feet).
# Between passes the ball sits at the current holder's feet.
PASSES = [
    ("H6", 0.6, "H8", 1.4, None),
    ("H8", PASS_T, "H11", RECEIVE_T, TARGET),
]
SHOT = ("H11", SHOT_T, GOAL_T, GOAL_POINT)  # shooter, shot t, goal t, where the ball ends
FOOT = 0.7  # ball sits just ahead of a player's feet


def interp(keys, t):
    """Catmull-Rom through the keyframes: passes through each one with continuous velocity."""
    if len(keys) == 1 or t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    if t >= keys[-1][0]:
        return keys[-1][1], keys[-1][2]
    i = next(i for i in range(len(keys) - 1) if t <= keys[i + 1][0])
    p0, p1, p2, p3 = keys[max(i - 1, 0)], keys[i], keys[i + 1], keys[min(i + 2, len(keys) - 1)]
    u = (t - p1[0]) / (p2[0] - p1[0])
    # Scale tangents by segment duration so uneven keyframe spacing does not overshoot.
    dt = p2[0] - p1[0]

    def axis(k):
        m1 = (p2[k] - p0[k]) / (p2[0] - p0[0]) * dt if p2[0] > p0[0] else 0.0
        m2 = (p3[k] - p1[k]) / (p3[0] - p1[0]) * dt if p3[0] > p1[0] else 0.0
        h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
        return h00 * p1[k] + h10 * m1 + h01 * p2[k] + h11 * m2

    return axis(1), axis(2)


def lerp(a, b, f):
    return a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])


def at_feet(pid, t):
    x, y = interp(HOME[pid], t)
    return x + FOOT, y


def ball_at(t):
    for passer, t_pass, receiver, t_recv, end in PASSES:
        if t <= t_pass:
            return at_feet(passer, t)
        if t <= t_recv:
            return lerp(at_feet(passer, t_pass), end or at_feet(receiver, t_recv), (t - t_pass) / (t_recv - t_pass))
    shooter, t_shot, t_goal, goal = SHOT
    if t <= t_shot:
        return at_feet(shooter, t)
    if t <= t_goal:
        return lerp(at_feet(shooter, t_shot), goal, (t - t_shot) / (t_goal - t_shot))
    return goal


def _pt(p):
    return {"x": round(p[0], 1), "y": round(p[1], 1)}


def build():
    rng = random.Random(SEED)
    phase = {pid: (rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi))
             for pid in list(HOME) + list(AWAY)}
    frames = []
    n = int(DURATION * HZ)
    for i in range(n + 1):
        t = round(i / HZ, 3)
        players = []
        for team, roster in (("HOME", HOME), ("AWAY", AWAY)):
            for pid, keys in roster.items():
                x, y = interp(keys, t)
                px, py = phase[pid]
                x += SWAY_M * math.sin(0.9 * t + px) + rng.uniform(-NOISE_M, NOISE_M)
                y += SWAY_M * math.sin(0.7 * t + py) + rng.uniform(-NOISE_M, NOISE_M)
                players.append({"id": pid, "team": team, "x": round(x, 2), "y": round(y, 2)})
        bx, by = ball_at(t)
        frames.append({"t": t, "ball": {"x": round(bx, 2), "y": round(by, 2)}, "players": players})

    events = []
    for passer, t_pass, receiver, t_recv, end in PASSES:
        end = end or at_feet(receiver, t_recv)
        events += [
            {"t": t_pass, "type": "PASS", "team": "HOME", "playerId": passer, "targetPlayerId": receiver,
             "start": _pt(at_feet(passer, t_pass)), "end": _pt(end), "outcome": "COMPLETE"},
            {"t": t_recv, "type": "RECEIVE", "team": "HOME", "playerId": receiver, "location": _pt(end)},
        ]
    shooter, t_shot, t_goal, _ = SHOT
    events += [
        {"t": t_shot, "type": "SHOT", "team": "HOME", "playerId": shooter, "location": _pt(at_feet(shooter, t_shot)),
         "outcome": "GOAL"},
        {"t": t_goal, "type": "GOAL", "team": "HOME", "playerId": shooter},
    ]

    return {
        "schemaVersion": "0.1",
        "scenarioId": "01_decoy_run",
        "description": "Synthetic 10 s sequence ending in a goal. Fictional clubs and players.",
        "pitch": {"length": 105, "width": 68},
        "sampleRateHz": HZ,
        "teams": {
            "HOME": {"name": "North London Red", "attacksTowards": "+x"},
            "AWAY": {"name": "South Coast Blue", "attacksTowards": "-x"},
        },
        "frames": frames,
        "events": events,
    }


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "01_decoy_run.json"
    out.write_text(json.dumps(build(), indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
