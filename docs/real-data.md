# Testing on real tracking data

The detectors were built on a scripted synthetic scenario. To check they were not just tuned to it, we ran them on
real match tracking data, reviewed what they found, and fixed the rules where review showed they were wrong.

## Data

**Metrica Sports sample data, game 2** ([github.com/metrica-sports/sample-data](https://github.com/metrica-sports/sample-data)):
one full match of player and ball tracking at 25 Hz with a synchronised event log. Teams, players and competition are
anonymised. Metrica asks that public use acknowledges the source, which this page does. The raw files are downloaded
into the git-ignored `external-data/` folder and are not part of this repository.

## Method

1. `scripts/convert_metrica.py` cuts one clip per shot (all **24** shots): the 25 s before it and 2 s after, from the
   same half, converted to our format (`docs/data-model.md`): 5 Hz, metres with y up, the shooting team labelled
   HOME and rotated to attack +x, goalkeepers numbered 1, passes as `PASS` + `RECEIVE`, recoveries as
   `POSSESSION_CHANGE`.
2. `scripts/analyse_clips.py` runs every detector on every clip. The detectors are the same code as for the synthetic
   demo; they read only positions and events.
3. Candidates were reviewed by eye in the replay (`?scenario=metrica_g2_shot_12` when the local data is present)
   and, for Sequence Origin, checked against Metrica's full event log for changes of possession.

## What review found, and what changed

| Detector | First run | Problem found | Rule change | After |
|---|---|---|---|---|
| Space Creator | 9 detections | After a long switch of play the whole defence ends up further from the receiving spot, so up to five runners were credited for the same space; one "created" space that never grew (1.0×) | The dragged defender must have been guarding the receiving spot (within 2 m of the nearest defender to it), and the space must grow at least 1.5× | 2 |
| Sequence Origin | 12 detections | One chain ran across a turnover: the attackers lost the ball and won it back, and a pass from before the turnover was credited | A chance can only begin after the attacking team last won the ball | 11 |
| Sequence Origin | 11 detections | Moves ending in a cut-back were rejected outright: the assist goes backwards, which failed the "attack keeps moving forward" check, even though a cut-back from the byline is one of the most common final balls | The assist itself is exempt from the forward check; earlier passes still are not | 15 |

All three changes are covered by tests (`backend/tests/test_space_creator.py`, `backend/tests/test_sequence_origin.py`),
and the synthetic decoy run still gives exactly the same insights.

## Results after the fixes

24 shots; 15 have at least one detection.

**Space Creator (2)**

| Clip | Detection | Verdict |
|---|---|---|
| shot 12 | H10 drags A3 11.8 m from the receiving spot; space 34 → 252 m² (7.5×); H10 never touches the ball | **Genuine decoy run**: the same pattern as the synthetic scenario |
| shot 05 | H7 drags A6 4.1 m; space ×21 | **Ambiguous**: A6 was guarding the spot and was pulled, but most of the space came from a cross switching play, so the ratio overstates H7's effect |

**Sequence Origin (15)**: every chain is one continuous possession (checked against the event log). Origins range
from 0.9 s to 14.8 s before the shot. The four added by the cut-back fix (shots 01, 06, 12, 21) all end with an assist
played back 8–14 m from near the byline to a teammate at the edge of the box. Three were reviewed by eye:

| Clip | Detection | Verdict |
|---|---|---|
| shot 16 | H5's long pass up the right channel bypasses 6 opponents, 3.6 s before the shot | **Plausible origin** |
| shot 12 | H8's pass bypasses 5 opponents 6.5 s before the shot; the move ends with H5's cut-back to H8 into the space H10's run opened | **Plausible origin**, shown on the live site alongside the Space Creator insight |
| shot 08 | H3's forward pass into H10 between the lines bypasses 3, 12.4 s before the shot | **Plausible but generous**: one bypassed opponent was far across the pitch |

## Known limits

- **Space ratio is the total change at the spot**, not the runner's share of it; a switch of play can inflate it.
- **"Bypassed" only checks who is goal-side of the ball**, not how close they were, so distant opponents can count.
- Sequence Origin looks back at most **15 s**, so long build-ups are cut there.
- One match (24 shots) is a small sample; the remaining detections were not all reviewed by eye.

## Reproduce

```bash
mkdir -p external-data/metrica/sample_game_2   # download the three Sample_Game_2 CSVs from the Metrica repo here
python3 -I scripts/convert_metrica.py external-data/metrica/sample_game_2 external-data/metrica/clips
python3 scripts/analyse_clips.py external-data/metrica/clips
```
