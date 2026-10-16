"""Generate scenario 01: a decoy run that opens space for a goal.

This script only emits raw tracking frames and events. It contains no detection logic and writes no
insight labels; the analysis engine has to find the pattern on its own.

Pitch: 105 x 68 m. HOME attacks toward +x.
"""
import json
import math
import random
import sys
from pathlib import Path

HZ = 5
DURATION = 10.0  # seconds
SEED = 7
NOISE_M = 0.12

# Keyframes: player -> list of (t, x, y). Linear interpolation between keyframes.
# Players with a single keyframe hold position (plus small noise).
HOME = {
    "H1": [(0, 38, 34)],
    "H2": [(0, 56, 10)],
    "H3": [(0, 56, 58)],
    "H4": [(0, 58, 30)],
    "H5": [(0, 54, 27)],
    "H6": [(0, 54, 41)],
    "H7": [(0, 76, 60)],
    "H8": [(0, 64, 34), (6.0, 66, 34), (10, 66, 34)],  # ball carrier, passes at t=6
    "H9": [(0, 92, 30)],
    # Decoy runner: starts the diagonal run toward the right touchline at t=1
    "H10": [(0, 76, 41), (1.0, 76, 41), (5.0, 85, 53), (10, 85, 53)],
    # Late runner from the left, receives at t=7.4
    "H11": [(0, 72, 14), (2.0, 72, 14), (3.5, 78, 22), (5.5, 85, 31), (7.4, 88, 36), (8.2, 89, 36), (10, 89, 36)],
}
AWAY = {
    "A1": [(0, 102, 34)],
    "A2": [(0, 82, 12)],
    "A3": [(0, 82, 58)],
    "A4": [(0, 70, 22)],
    "A5": [(0, 82, 24)],
    # Right-sided centre-back follows the decoy runner
    "A6": [(0, 82, 41), (1.0, 82, 41), (5.0, 85.5, 50.5), (10, 85.5, 50.5)],
    "A7": [(0, 60, 46)],
    "A8": [(0, 70, 34)],
    "A9": [(0, 60, 22)],
    "A10": [(0, 70, 46)],
    "A11": [(0, 60, 34)],
}
BALL = [
    (0, 64, 34), (6.0, 66, 34),      # carried by H8
    (7.4, 88, 36),                   # pass to H11
    (8.2, 89, 36),                   # H11 controls
    (8.9, 105, 34), (10, 105, 34),   # shot into the net
]


def interp(keys, t):
    if len(keys) == 1 or t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            return x0 + f * (x1 - x0), y0 + f * (y1 - y0)
    return keys[-1][1], keys[-1][2]


def build():
    rng = random.Random(SEED)
    frames = []
    n = int(DURATION * HZ)
    for i in range(n + 1):
        t = round(i / HZ, 3)
        players = []
        for team, roster in (("HOME", HOME), ("AWAY", AWAY)):
            for pid, keys in roster.items():
                x, y = interp(keys, t)
                x += rng.uniform(-NOISE_M, NOISE_M)
                y += rng.uniform(-NOISE_M, NOISE_M)
                players.append({"id": pid, "team": team, "x": round(x, 2), "y": round(y, 2)})
        bx, by = interp(BALL, t)
        frames.append({"t": t, "ball": {"x": round(bx, 2), "y": round(by, 2)}, "players": players})

    events = [
        {"t": 6.0, "type": "PASS", "team": "HOME", "playerId": "H8", "targetPlayerId": "H11",
         "start": {"x": 66, "y": 34}, "end": {"x": 88, "y": 36}, "outcome": "COMPLETE"},
        {"t": 7.4, "type": "RECEIVE", "team": "HOME", "playerId": "H11", "location": {"x": 88, "y": 36}},
        {"t": 8.2, "type": "SHOT", "team": "HOME", "playerId": "H11", "location": {"x": 89, "y": 36},
         "outcome": "GOAL"},
        {"t": 8.9, "type": "GOAL", "team": "HOME", "playerId": "H11"},
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
