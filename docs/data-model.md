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
  "t": 10.0,
  "team": "HOME",
  "playerId": "H10",
  "markerId": "A6",
  "targetZone": "central lane, penalty area",
  "confidence": 0.69,
  "confidenceParts": {
    "pull": 0.49,
    "follow": 1.0,
    "free": 0.65
  },
  "evidence": {
    "runnerDisplacementM": 14.2,
    "markerDisplacementM": 7.2,
    "markerFollowCosine": 1.0,
    "markerDistanceToTargetStartM": 5.4,
    "markerDistanceToTargetEndM": 9.3,
    "nearestDefenderToTargetStartM": 5.4,
    "nearestDefenderToTargetEndM": 9.3,
    "shotSecondsAfterPass": 2.2,
    "runnerTouches": 0,
    "freeSpaceStartM2": 93,
    "freeSpaceEndM2": 274,
    "freeSpaceGainM2": 181,
    "freeSpaceRatio": 2.9,
    "markerPullM": 3.9
  }
}
```

A Sequence Origin insight (see `docs/detection-rules.md`) adds who started the move and which opponents
it took out:

```json
{
  "type": "SEQUENCE_ORIGIN",
  "t": 6.4,
  "team": "HOME",
  "playerId": "H8",
  "partnerId": "H6",
  "pattern": "ONE_TWO",
  "bypassedIds": [
    "A10",
    "A11"
  ],
  "confidence": 0.78,
  "confidenceParts": {
    "lines": 0.67,
    "progress": 0.96
  },
  "evidence": {
    "opponentsBypassed": 2,
    "lineBreakingPassT": 7.1,
    "passesToShot": 3,
    "progressionM": 24.0,
    "secondsBeforeFinalPass": 3.6,
    "secondsBeforeShot": 5.8
  }
}
```

Every insight must carry numeric evidence so downstream AI can explain it without guessing.
