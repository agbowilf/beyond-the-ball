"""Generate scenario 02: a striker's run in behind opens the cut-back zone.

This script only emits raw tracking frames and events. It contains no detection logic and writes no
insight labels; the analysis engine has to find the pattern on its own.

Pitch: 105 x 68 m. HOME attacks toward +x; low y is HOME's right.

Story: HOME's centre-backs circulate the ball (H5 to H4, then into H6). H6 plays a single pass through the AWAY
midfield line to H8, who feeds H11 running down the right. As H11 reaches the byline, striker H9 attacks the near
post and centre-back A5 goes with them, so the back line drops deep and the space at the edge of the box empties.
H11 cuts the ball back to H10, arriving late from midfield, who finishes past the keeper into the far corner. Every
attacker is level with or behind the AWAY back line, or behind the ball, until the final pass.
"""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_decoy_run import interp, lerp  # noqa: E402  (shared Catmull-Rom movement and ball helpers)

HZ = 5
DURATION = 14.0  # seconds
SEED = 11
NOISE_M = 0.06
SWAY_M = 0.25
FOOT = 0.7

# Keyframes: player -> list of (t, x, y), absolute times.
HOME = {
    "H1": [(0, 38, 34), (7, 41, 34), (14, 44, 34)],
    "H2": [(0, 58, 8), (4, 62, 7), (8, 70, 7), (14, 77, 9)],          # right back pushes on behind H11
    "H3": [(0, 58, 60), (7, 62, 60), (14, 66, 59)],
    "H4": [(0, 46, 27), (0.4, 46.2, 27), (1.2, 46.5, 27), (2.0, 47.5, 27.2), (5, 51, 27.5), (14, 56, 28)],
    "H5": [(0, 46, 41), (0.4, 46.3, 41), (2.5, 48, 40.5), (14, 55, 39)],
    # Central midfielder: receives from H4, then plays the pass through the midfield line
    "H6": [(0, 54, 35), (2.0, 56, 33.5), (2.8, 57, 32.5), (4.6, 59.5, 31), (7, 62, 31), (14, 67, 32)],
    "H7": [(0, 74, 60), (7, 79, 58), (14, 86, 55)],                    # left winger holds the far side
    # Attacking midfielder: drops between the lines, receives behind the AWAY midfield, feeds H11
    "H8": [(0, 69, 31.5), (2.4, 71, 30), (4.6, 73.5, 28.5), (5.4, 75.5, 27.5), (6.2, 78, 24.5), (7.0, 80, 22.5),
           (8.2, 82.5, 23.5), (10.0, 85, 25.5), (14, 87, 27)],
    # Striker: holds the line, then attacks the near post as H11 reaches the byline
    "H9": [(0, 83, 31.5), (4.4, 84.5, 31), (6.0, 87, 30.5), (7.6, 91.5, 29.5), (9.4, 96, 28.5), (11, 97.5, 29),
           (14, 98, 30)],
    # Late runner: arrives from midfield into the cut-back zone at the edge of the box
    "H10": [(0, 69, 44), (4.0, 71, 42), (6.5, 75.5, 39.5), (8.2, 80.5, 36.5), (9.4, 84.5, 33.5), (10.2, 87.5, 31.5),
            (10.8, 88.5, 31.2), (14, 91, 31.5)],
    # Right winger: runs onto H8's pass down the line, carries to the byline, cuts it back
    "H11": [(0, 79, 12), (4.0, 80.5, 11.5), (6.0, 84, 10), (7.0, 86.5, 9.2), (7.8, 89.5, 8.6), (8.6, 95, 9.6),
            (9.4, 100, 11.5), (10.4, 101.5, 13), (14, 100, 15)],
}
AWAY = {
    # Keeper shifts to the near post for the cut-back threat, then dives across too late
    "A1": [(0, 100, 34), (8.0, 100.5, 31.5), (9.4, 101.8, 29.5), (10.2, 101.6, 30.6), (10.8, 101.8, 31.2),
           (11.5, 102.8, 32.6), (14, 103, 32.8)],
    # Left back: chases H11 down the line, a step behind
    "A2": [(0, 84.5, 13.5), (4.0, 85, 12.8), (6.0, 86.5, 11.5), (7.8, 90, 11.6), (9.4, 96.5, 14.4), (14, 99, 17)],
    # Centre-back: marks H9 and goes with the near-post run, goal-side, leaving the edge of the box
    "A5": [(0, 85, 28.5), (4.4, 86.3, 28.6), (6.0, 88.8, 28.9), (7.6, 93.3, 27.9), (9.4, 97.6, 28.0), (11, 99.5, 27.5),
           (14, 100, 29)],
    # Other centre-back: drops to protect the far post
    "A6": [(0, 85, 39), (4.4, 86, 38.5), (7.0, 89.5, 37), (9.4, 94.5, 36), (11, 96, 35.5), (14, 97, 35)],
    "A3": [(0, 84, 56), (7, 88, 53), (14, 94, 49)],                    # right back stays with H7
    # Midfield four: bypassed by H6's pass, then sprint back
    "A4": [(0, 72, 20), (4.6, 72, 19), (7.0, 76.5, 18.5), (9.4, 83, 19), (14, 89, 21)],
    "A8": [(0, 72, 33), (4.6, 71.5, 33.5), (6.0, 73.5, 32.5), (7.0, 75.5, 31), (9.4, 80.5, 29), (14, 87, 30)],
    "A10": [(0, 72, 41), (4.6, 71, 38.5), (7.0, 74.3, 41), (9.4, 80.5, 38.5), (10.8, 84, 36.5), (14, 88.5, 35)],
    "A7": [(0, 72, 51), (7, 76, 48), (14, 84, 45)],
    # Front two: hold their shape ahead of the ball during the build-up
    "A9": [(0, 62, 28), (2.0, 61, 29), (2.8, 61.5, 29.5), (4.6, 62.5, 29.5), (7, 64, 28), (14, 69, 29)],
    "A11": [(0, 64, 40), (2.8, 63, 38.5), (4.6, 63.5, 37.5), (14, 70, 38)],
}

PASS_T, RECEIVE_T, SHOT_T, GOAL_T = 9.4, 10.2, 10.8, 11.5
TARGET = (87.6, 31.5)  # the cut-back zone at the edge of the box
GOAL_POINT = (106.0, 36.9)  # far corner, inside the post (y = 37.66)

# Ball possession plan: (passer, pass t, receiver, receive t, end point or None for the receiver's feet).
PASSES = [
    ("H5", 0.4, "H4", 1.2, None),     # build-up across the back...
    ("H4", 2.0, "H6", 2.8, None),     # ...and into midfield
    ("H6", 4.6, "H8", 5.4, None),     # single pass through the midfield line
    ("H8", 7.0, "H11", 7.8, None),    # out to the right winger
    ("H11", PASS_T, "H10", RECEIVE_T, TARGET),  # cut-back from the byline
]
SHOT = ("H10", SHOT_T, GOAL_T, GOAL_POINT)


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
    phase = {pid: (rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)) for pid in list(HOME) + list(AWAY)}
    frames = []
    for i in range(int(DURATION * HZ) + 1):
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
        "scenarioId": "02_cutback",
        "description": "Synthetic 14 s sequence ending in a goal from a cut-back. Fictional clubs and players.",
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
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "02_cutback.json"
    out.write_text(json.dumps(build(), indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
