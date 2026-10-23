"""Convert Metrica Sports sample tracking and event data into Beyond the Ball scenario clips.

Source: https://github.com/metrica-sports/sample-data (anonymised; "if you use it for anything public, please
acknowledge the source"). Raw files are downloaded into external-data/ (git-ignored) and never committed.

One clip per shot: the 15 s before it plus 2 s after, from the same half, downsampled from 25 Hz to 5 Hz and
mapped to our format (docs/data-model.md):

- metres on a 105 x 68 m pitch with y pointing up (Metrica's origin is the top left, y pointing down);
- the shooting team is labelled HOME and the clip is rotated so it attacks +x, as our format requires;
- each team's goalkeeper becomes shirt 1 (detectors exclude H1/A1), other players 2, 3, ... by Metrica number;
- passes become PASS plus RECEIVE events, shots become SHOT (plus GOAL when scored).

Standard library only. Usage:
    python3 -I scripts/convert_metrica.py external-data/metrica/sample_game_2 external-data/metrica/clips
"""
import csv
import json
import math
import sys
from pathlib import Path

SOURCE_HZ = 25
STEP = 5  # keep every 5th frame: 25 Hz -> 5 Hz
BEFORE_S, AFTER_S = 15.0, 2.0
LENGTH, WIDTH = 105.0, 68.0
MIN_PRESENCE = 0.95  # players on the pitch for less of the clip (substitutions) are left out


def read_tracking(path):
    """frame -> (period, {player: (x, y) or None}, ball (x, y) or None), keeping every STEP-th frame."""
    with open(path, newline="") as f:
        rows = csv.reader(f)
        next(rows)
        next(rows)
        header = next(rows)
        cols = [(i, name) for i, name in enumerate(header) if name.startswith("Player") or name == "Ball"]
        out = {}
        for row in rows:
            frame = int(row[1])
            if frame % STEP:
                continue
            pos = {}
            for i, name in cols:
                x, y = row[i], row[i + 1]
                pos[name] = (float(x), float(y)) if x not in ("", "NaN") and y not in ("", "NaN") else None
            ball = pos.pop("Ball", None)
            out[frame] = (int(row[0]), pos, ball)
    return out


def read_events(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def to_metres(x, y, rotate):
    """Metrica 0..1 (origin top left, y down) to our metres (y up); rotate 180 degrees if needed."""
    mx, my = x * LENGTH, (1 - y) * WIDTH
    return (LENGTH - mx, WIDTH - my) if rotate else (mx, my)


def goalkeepers(tracking, team_players, period):
    """Per team, the player who stays furthest from the halfway line on average in that half."""
    keepers, sides = {}, {}
    for team, players in team_players.items():
        best = None
        for p in players:
            xs = [pos[p][0] for per, pos, _ in tracking.values() if per == period and pos.get(p)]
            if len(xs) < 100:
                continue
            mean_x = sum(xs) / len(xs)
            if best is None or abs(mean_x - 0.5) > abs(best[1] - 0.5):
                best = (p, mean_x)
        keepers[team], sides[team] = best[0], best[1]
    return keepers, sides


def outcome(subtype):
    s = subtype.upper()
    return "GOAL" if "GOAL" in s else "SAVED" if "SAVED" in s else "MISSED"


def convert_clip(index, shot, tracking, events, team_players):
    period = int(shot["Period"])
    shooting = shot["Team"]
    other = "Away" if shooting == "Home" else "Home"
    keepers, keeper_x = goalkeepers(tracking, team_players, period)
    # The shooting team attacks away from its own keeper; our format needs it attacking +x.
    rotate = keeper_x[shooting] > 0.5

    shot_frame = int(shot["Start Frame"])
    first = shot_frame - int(BEFORE_S * SOURCE_HZ)
    last = shot_frame + int(AFTER_S * SOURCE_HZ)
    frames = [f for f in range(first - first % STEP + STEP, last + 1, STEP)
              if f in tracking and tracking[f][0] == period]
    if len(frames) < 20:
        return None

    # Player ids: keeper is 1, others numbered by Metrica number; HOME = shooting team.
    ids = {}
    for team, label in ((shooting, "H"), (other, "A")):
        present = [p for p in team_players[team]
                   if sum(tracking[f][1].get(p) is not None for f in frames) >= MIN_PRESENCE * len(frames)]
        outfield = sorted((p for p in present if p != keepers[team]), key=lambda p: int(p[6:]))
        if keepers[team] in present:
            ids[keepers[team]] = f"{label}1"
        for n, p in enumerate(outfield, start=2):
            ids[p] = f"{label}{n}"

    out_frames, last_pos, last_ball = [], {}, None
    for f in frames:
        _, pos, ball = tracking[f]
        if ball is not None:
            last_ball = ball
        players = []
        for p, pid in ids.items():
            xy = pos.get(p) or last_pos.get(p)
            if xy is None:  # missing from the very first frames: borrow the next known position
                xy = next(tracking[g][1][p] for g in frames if tracking[g][1].get(p))
            last_pos[p] = xy
            x, y = to_metres(*xy, rotate)
            players.append({"id": pid, "team": "HOME" if pid[0] == "H" else "AWAY", "x": round(x, 2), "y": round(y, 2)})
        bx, by = to_metres(*(last_ball or (0.5, 0.5)), rotate)
        out_frames.append({"t": round((f - frames[0]) / SOURCE_HZ, 2), "ball": {"x": round(bx, 2), "y": round(by, 2)},
                           "players": players})

    def t(frame):
        return round((int(frame) - frames[0]) / SOURCE_HZ, 2)

    def pt(x, y):
        if x in ("", "NaN") or y in ("", "NaN"):
            return None
        mx, my = to_metres(float(x), float(y), rotate)
        return {"x": round(mx, 1), "y": round(my, 1)}

    out_events = []
    for e in events:
        if int(e["Period"]) != period or not frames[0] <= int(e["Start Frame"]) <= frames[-1]:
            continue
        team = "HOME" if e["Team"] == shooting else "AWAY"
        if e["Type"] == "PASS" and e["From"] in ids and e["To"] in ids and pt(e["End X"], e["End Y"]):
            out_events.append({"t": t(e["Start Frame"]), "type": "PASS", "team": team, "playerId": ids[e["From"]],
                               "targetPlayerId": ids[e["To"]], "start": pt(e["Start X"], e["Start Y"]),
                               "end": pt(e["End X"], e["End Y"]), "outcome": "COMPLETE"})
            out_events.append({"t": t(e["End Frame"]), "type": "RECEIVE", "team": team, "playerId": ids[e["To"]],
                               "location": pt(e["End X"], e["End Y"])})
        elif e["Type"] == "SHOT" and e["From"] in ids and pt(e["Start X"], e["Start Y"]):
            result = outcome(e["Subtype"])
            out_events.append({"t": t(e["Start Frame"]), "type": "SHOT", "team": team, "playerId": ids[e["From"]],
                               "location": pt(e["Start X"], e["Start Y"]), "outcome": result})
            if result == "GOAL":
                out_events.append({"t": t(e["End Frame"]), "type": "GOAL", "team": team, "playerId": ids[e["From"]]})
    out_events.sort(key=lambda ev: ev["t"])

    return {
        "schemaVersion": "0.1",
        "scenarioId": f"metrica_g2_shot_{index:02d}",
        "description": f"Real tracking data: Metrica Sports sample game 2 (anonymised), the {BEFORE_S:.0f} s before "
                       f"shot {index} ({outcome(shot['Subtype']).lower()}).",
        "pitch": {"length": LENGTH, "width": WIDTH},
        "sampleRateHz": SOURCE_HZ // STEP,
        "teams": {
            "HOME": {"name": f"Metrica {shooting} (anonymised)", "attacksTowards": "+x"},
            "AWAY": {"name": f"Metrica {other} (anonymised)", "attacksTowards": "-x"},
        },
        "frames": out_frames,
        "events": out_events,
        # Provenance only; detectors never read it.
        "source": {
            "dataset": "Metrica Sports sample data, game 2 (https://github.com/metrica-sports/sample-data)",
            "period": period,
            "shotFrame": shot_frame,
            "players": {pid: f"{team} {p}" for team in (shooting, other) for p, pid in ids.items()
                        if p in team_players[team]},
        },
    }


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    home = read_tracking(next(src.glob("*Tracking*Home*.csv")))
    away = read_tracking(next(src.glob("*Tracking*Away*.csv")))
    tracking = {f: (home[f][0], {**home[f][1], **away[f][1]}, home[f][2] or away[f][2]) for f in home if f in away}
    team_players = {"Home": sorted(next(iter(home.values()))[1]), "Away": sorted(next(iter(away.values()))[1])}
    events = read_events(next(src.glob("*Events*.csv")))
    shots = [e for e in events if e["Type"] == "SHOT"]
    for i, shot in enumerate(shots, start=1):
        clip = convert_clip(i, shot, tracking, events, team_players)
        if clip is None:
            print(f"shot {i}: skipped (too close to the start of a half)")
            continue
        path = out / f"{clip['scenarioId']}.json"
        path.write_text(json.dumps(clip, separators=(",", ":")))
        print(f"shot {i:2d}: {shot['Team']:<4} {shot['Subtype']:<22} {len(clip['frames'])} frames, "
              f"{len(clip['events'])} events -> {path.name}")


if __name__ == "__main__":
    main()
