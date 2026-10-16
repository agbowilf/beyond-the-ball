# Beyond the Ball

AI-powered football intelligence that explains what happens *around* the ball.

Built for the Microsoft x Premier League **Inside the Game: Developer Hackathon**.

Most football analytics describe what happened to the ball: the pass, the shot, the goal. Beyond the Ball
analyses synthetic event and positional tracking data to surface the off-ball actions that made those moments possible.

## Insight types (V1 target)

| Insight | Status |
|---|---|
| Space Creator: an off-ball run drags a defender away and opens usable space | In progress (first detector working) |
| Pressing Contributor: positioning removes a passing option and forces a turnover | Planned |
| Sequence Origin: the action where a chance really began | Planned |
| Match Shift: a material change in how the teams behave | Planned |

## Architecture

```
Synthetic scenario generator
        |
Event stream + positional tracking stream
        |
Deterministic analysis engine (Python)   <- does the football reasoning
        |
Structured insights (JSON, with numeric evidence)
        |
Microsoft Foundry agents                 <- explain and personalise only
        |
React pitch visualisation
```

The generator knows nothing about the detection rules, and the detector only sees raw positions and events.
The AI layer never invents tactical claims; it only explains findings that already carry numeric evidence.

## Repo layout

```
docs/                  architecture notes, data model, detection rules
scenarios/             scripted synthetic scenarios (generator + generated JSON)
backend/analysis/      deterministic detectors
backend/tests/         pytest suite
frontend/              React visualisation (not started)
```

## Quick start

```bash
pip install pytest
python scenarios/generate_decoy_run.py        # writes scenarios/01_decoy_run.json
python backend/run_analysis.py scenarios/01_decoy_run.json
pytest backend/tests
```

## Status

Early development. See `docs/data-model.md` for the schema and `docs/detection-rules.md` for how Space Creator is detected.
All clubs, players and data are synthetic.
