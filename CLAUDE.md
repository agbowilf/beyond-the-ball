# CLAUDE.md

Context for Claude Code sessions working in this repo.

## Project

**Beyond the Ball**: an entry for the Microsoft x Premier League **"Inside the Game"** developer hackathon.
It explains the off-ball football that stats miss (decoy runs, pressing, where a chance really began) using
**synthetic** tracking and event data. All clubs, players and data are fictional.

Pipeline:

```
scenarios/generate_*.py   -> scenarios/*.json            (frames + events, no labels)
backend/analysis/*.py     -> insights JSON               (deterministic, with numeric evidence)
Microsoft Foundry agents  -> explanations / personalisation (planned; explain only, never invent claims)
frontend/ (Vite + React)  -> pitch replay highlighting the insight
```

## Hackathon constraints

- **Deadline:** submissions close **Oct 27, 2026, 11:59pm Pacific**.
- Must use the featured Microsoft tech (**Microsoft Foundry, Agent Framework, Azure**) to pass Stage One.
  Python and React are allowed alongside it. Foundry integration is not built yet and is required.
- Submission needs: a **public GitHub repo** (github.com/agbowilf/beyond-the-ball), a **demo video under 2 minutes**,
  and **working judge access** (a deployed or easily runnable demo).

## Working rules

- **Commits:** small, meaningful, Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`).
  The git history is part of the submission, so one logical change per commit.
- **Never push** without asking the user first.
- Work on a feature branch per issue (`feat/...`) and merge through a PR that references it; CI must be green.
- Detectors read only `frames` and `events`, never scenario metadata or labels. Thresholds live as module constants
  and are documented in `docs/detection-rules.md`; keep the two in sync.
- The AI layer only phrases findings that already carry numeric evidence. Football reasoning stays in Python.
- The frontend does not re-implement detection; it renders scenario JSON plus insights produced by the backend.

## Layout

| Path | What |
|---|---|
| `docs/data-model.md` | Schema: 105 x 68 m pitch, HOME attacks +x, 5 Hz frames, events, insight output shape |
| `docs/detection-rules.md` | Space Creator rules, thresholds, confidence formula, known limits |
| `docs/architecture.md` | Pipeline and principles |
| `scenarios/generate_decoy_run.py` | Seeded generator for `scenarios/01_decoy_run.json` (10 s, 51 frames, H8 -> H11 pass at t=6.0, goal) |
| `backend/analysis/space_creator.py` | Space Creator detector; finds **H10** dragging marker **A6**, confidence **0.90** |
| `backend/analysis/sequence_origin.py` | Sequence Origin detector; finds the **H8-H6 one-two** at 2.4 s taking out A10 and A11, confidence **0.78** |
| `backend/run_analysis.py` | Runs all detectors on a scenario, prints insights JSON |
| `backend/tests/` | pytest suite |
| `scenarios/01_decoy_run.insights.json` | Committed detector output the frontend renders; regenerate when detectors change |
| `frontend/src/` | `data.js` (loads JSON, interpolates frames), `Pitch`, `EvidencePanel` (shared), `Controls` + `useReplay`, `OffsideLine` |
| `frontend/src/views/` | One view per insight type (overlay, panel body, wording) registered in `views/index.js`; `?insight=N&t=S` opens a tab at a time |

## Commands

```bash
python scenarios/generate_decoy_run.py                       # regenerate scenario JSON
python backend/run_analysis.py scenarios/01_decoy_run.json   # print insights
pytest backend/tests                                         # run tests
python backend/run_analysis.py scenarios/01_decoy_run.json > scenarios/01_decoy_run.insights.json
cd frontend && npm install && npm run dev                    # pitch replay (?t=6 jumps to the pass)
cd frontend && npm run lint && npm run build
```

## Status

Done (v0.1, tagged): realistic decoy-run scenario, Space Creator detector, React replay with evidence panel, CI.
Done on `feat/sequence-origin` (#1): Sequence Origin detector, tests, and a replay tab for it.

Roadmap is tracked in GitHub issues: #2 Foundry agents that explain insights, #3 Pressing Contributor detector,
#4 Azure deployment for judge access. Match Shift is post-hackathon (needs match-length data); README roadmap only.
Then README, pitch and demo video before the deadline.
