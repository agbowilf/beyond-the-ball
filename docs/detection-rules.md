# Detection rules

All detectors are deterministic. They read only raw frames and events, never scenario labels.

## Space Creator (v0.1)

Goal: find an off-ball run by an attacker that dragged a defender away from the zone later used to receive a
pass that led to a shot.

### Trigger

A `PASS` by team T followed by a `SHOT` by the same team within **5 s** of the pass.
The pass end point is the **target zone**.

### Window

`[t_pass - 5 s, t_pass]`. Positions at the window start and at `t_pass` are compared.

### Candidate runners

Teammates of the passer who are not the passer or the receiver, and whose straight-line displacement over the
window is at least **6 m**.

### Marker

The opposing outfield player nearest to the runner at the window start.

### Checks (all must hold)

1. Marker displacement over the window is at least **4 m**.
2. Cosine similarity between runner and marker displacement vectors is at least **0.5** (the marker tracked the run).
3. The marker's distance to the target zone grew by at least **3 m** over the window.

### Evidence

| Field | Meaning |
|---|---|
| `runnerDisplacementM` | Runner straight-line displacement over the window |
| `markerDisplacementM` | Marker straight-line displacement over the window |
| `markerFollowCosine` | Direction similarity of runner and marker |
| `markerDistanceToTargetStartM` / `EndM` | Marker distance to the target zone before and after |
| `nearestDefenderToTargetStartM` / `EndM` | Nearest opposing outfield player to the target zone before and after |
| `shotSecondsAfterPass` | Delay between pass and shot |

### Confidence

```
pull   = clip((marker_end - marker_start) / 8, 0, 1)
follow = clip(cosine, 0, 1)
free   = clip((nearest_end - nearest_start) / 6, 0, 1)
confidence = 0.4*pull + 0.3*follow + 0.3*free
```

Weights are a v0.1 starting point and will be tuned against more scenarios.

### Known limits

- One marker per runner (nearest at window start). Zonal marking is not modelled.
- Goalkeepers are excluded from marker and nearest-defender checks.
- Only chances ending in a shot are considered.
