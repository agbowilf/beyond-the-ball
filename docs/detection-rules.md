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
4. The marker was guarding the target zone: at the window start it was within **2 m** of the nearest opposing
   outfield player to the zone (so pulling away a defender who was not covering the space earns no credit).
5. The free space at the target zone grew by at least **1.5×** (`freeSpaceRatio`); if no space opened, no space was
   created.

Checks 4 and 5 were added after running the detector on real tracking data, where they removed false positives
caused by long switches of play and by a second defender already covering the spot (see `docs/real-data.md`).

### Evidence

| Field | Meaning |
|---|---|
| `runnerDisplacementM` | Runner straight-line displacement over the window |
| `markerDisplacementM` | Marker straight-line displacement over the window |
| `markerFollowCosine` | Direction similarity of runner and marker |
| `markerDistanceToTargetStartM` / `EndM` | Marker distance to the target zone before and after |
| `nearestDefenderToTargetStartM` / `EndM` | Nearest opposing outfield player to the target zone before and after |
| `shotSecondsAfterPass` | Delay between pass and shot |
| `runnerTouches` | Times the runner played, received or shot the ball from the window start to the shot (`PASS`, `RECEIVE`, `SHOT` events) |
| `freeSpaceStartM2` / `EndM2` | Free space at the target zone before and after: the area of the circle around it, out to the nearest opposing outfield player (`π × nearestDefenderToTarget²`) |
| `freeSpaceGainM2` | `freeSpaceEndM2 - freeSpaceStartM2` |
| `freeSpaceRatio` | `freeSpaceEndM2 / freeSpaceStartM2`, from the unrounded areas ("4.9× more receiving space") |
| `markerPullM` | How much further the marker ended from the target zone: `markerDistanceToTargetEndM - markerDistanceToTargetStartM` |
| `backLineDropM` | How far the defending back line dropped towards its own goal over the window: change in the mean depth of its four deepest outfield players (negative if it stepped up). It describes the line during the run; it does not say the run alone caused it |

### Target zone label

`targetZone` names where the pass was received, from the attacking team's point of view, using the standard five
lanes (split at the penalty-area and goal-area edges, y = 13.84, 24.84, 43.16 and 54.16 m) and the area of the
pitch: `"<lane>, <area>"`, for example `"central lane, penalty area"`. Lanes are `left wing`, `left half-space`,
`central lane`, `right half-space` and `right wing`; areas are `penalty area`, `attacking third`, `middle third` or
`defensive third`. HOME attacks +x, so HOME's left is high y.

### Confidence

```
pull   = clip((marker_end - marker_start) / 8, 0, 1)
follow = clip(cosine, 0, 1)
free   = clip((nearest_end - nearest_start) / 6, 0, 1)
confidence = 0.4*pull + 0.3*follow + 0.3*free
```

The three parts are reported as `confidenceParts` (`pull`, `follow`, `free`, each 0 to 1) so a reader can see why
the score is what it is.

Weights are a v0.1 starting point and will be tuned against more scenarios.

### Known limits

- One marker per runner (nearest at window start). Zonal marking is not modelled.
- Goalkeepers are excluded from marker and nearest-defender checks.
- Only chances ending in a shot are considered.

## Sequence Origin (v0.1)

Goal: find the action where a chance really began. That is often well before the assist: the pass that
first broke a line of the opponent's shape, after which the attack kept moving toward goal.

### Possession chain

Starting from a `SHOT`, walk back through completed `PASS` events by the same team: the pass whose
`targetPlayerId` is the current holder, then the pass to that pass's `playerId`, and so on, looking back at
most **15 s** before the shot, and never past the last `POSSESSION_CHANGE` won by the defending team (a chance
begins only after the attackers last won the ball). Each pass is received at the receiver's next `RECEIVE` event.

### Opponents bypassed

For each pass, an opposing outfield player is **goal-side** if they are nearer the attacked goal than the ball
(for HOME, `x` greater than the ball's `x`). A player is **bypassed** if goal-side in the frame when the pass is
played and not goal-side in the frame when it is received.

### Origin

The origin is the **earliest** pass in the chain that:

1. bypasses at least **2** opponents (it breaks a line), and
2. is followed only by passes that do not go backward by more than **2 m**, so the attack keeps progressing
   to the shot.

If that pass is the return of a wall pass (the previous pass in the chain went from its receiver to its
passer, within **2 s**), the origin is the first pass of that **one-two**, since the lay-off set it up.

### Output fields

| Field | Meaning |
|---|---|
| `playerId` | Who played the origin pass |
| `partnerId` | The other player in the one-two, or the receiver of a single line-breaking pass |
| `pattern` | `ONE_TWO` or `LINE_BREAKING_PASS` |
| `bypassedIds` | Opponents taken out by the line-breaking pass |

### Evidence

| Field | Meaning |
|---|---|
| `opponentsBypassed` | Number of opponents the line-breaking pass took out |
| `lineBreakingPassT` | When the line-breaking pass was played (the return, for a one-two) |
| `passesToShot` | Passes from the origin to the shot, origin included |
| `progressionM` | Distance gained toward goal from the origin pass to the shot |
| `secondsBeforeFinalPass` | How long before the assist the chance began |
| `secondsBeforeShot` | How long before the shot the chance began |

### Confidence

```
lines    = clip(opponents_bypassed / 3, 0, 1)
progress = clip(progression_m / 25, 0, 1)
confidence = 0.6*lines + 0.4*progress
```

Reported as `confidenceParts` (`lines`, `progress`).

Weights are a v0.1 starting point, like Space Creator's.

### Known limits

- A dribble that beats players is not counted; only passes can bypass opponents until carries are modelled
  as events.
- Goalkeepers are never counted as bypassed.
- One origin per shot; earlier line breaks in the same chain are not reported.
