# Data model (v0.1)

All data is synthetic. Fictional clubs and players only.

## Coordinate system

- Pitch is **105 m x 68 m**.
- `x` runs along the length (0 to 105), `y` across the width (0 to 68).
- The HOME team always attacks toward **+x** (goal centre at `x=105, y=34`).
- Units are metres and seconds.

## Scenario file

```json
{
  "schemaVersion": "0.1",
  "scenarioId": "01_decoy_run",
  "description": "...",
  "pitch": { "length": 105, "width": 68 },
  "sampleRateHz": 5,
  "teams": {
    "HOME": { "name": "North London Red", "attacksTowards": "+x" },
    "AWAY": { "name": "South Coast Blue", "attacksTowards": "-x" }
  },
  "frames": [ ... ],
  "events": [ ... ]
}
```

## Tracking frame (`frames[]`)

One snapshot at a fixed rate (5 Hz in v0.1).

```json
{
  "t": 4.2,
  "ball": { "x": 66.0, "y": 34.0 },
  "players": [
    { "id": "H10", "team": "HOME", "x": 78.1, "y": 46.3 }
  ]
}
```

- Player ids: `H1..H11` for HOME, `A1..A11` for AWAY.
- Possession is not stored in frames; it is derived from events.

## Event (`events[]`)

Events are sparse and timestamped on the same clock as frames (`t` in seconds).

| `type` | Required fields |
|---|---|
| `PASS` | `t`, `team`, `playerId`, `targetPlayerId`, `start{x,y}`, `end{x,y}`, `outcome` |
| `RECEIVE` | `t`, `team`, `playerId`, `location{x,y}` |
| `SHOT` | `t`, `team`, `playerId`, `location{x,y}`, `outcome` (`GOAL`, `SAVED`, `MISSED`) |
| `GOAL` | `t`, `team`, `playerId` |

Planned later: `TACKLE`, `PRESSURE`, `POSSESSION_CHANGE`, `SUBSTITUTION`.

## Insight output (produced by the analysis engine)

```json
{
  "type": "SPACE_CREATOR",
  "t": 6.0,
  "team": "HOME",
  "playerId": "H10",
  "markerId": "A6",
  "confidence": 0.92,
  "evidence": {
    "runnerDisplacementM": 15.1,
    "markerDisplacementM": 10.2,
    "markerFollowCosine": 0.95,
    "markerDistanceToTargetStartM": 7.7,
    "markerDistanceToTargetEndM": 14.7,
    "nearestDefenderToTargetStartM": 7.7,
    "nearestDefenderToTargetEndM": 13.4,
    "shotSecondsAfterPass": 2.2
  }
}
```

Every insight must carry numeric evidence so downstream AI can explain it without guessing.
