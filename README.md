# Beyond the Ball

**Football intelligence for what happens around the ball.** Beyond the Ball finds the off-ball work that stats miss,
such as a decoy run that drags a defender away and opens the space a goal comes from, then lets Microsoft Foundry
agents explain it for a fan, a coach or an analyst, with every claim checked against measured evidence.

Built for the Microsoft x Premier League **Inside the Game** developer hackathon.

**Try it:** [red-dune-0148df00f.1.azurestaticapps.net](https://red-dune-0148df00f.1.azurestaticapps.net)

| | |
|---|---|
| [Demo match](https://red-dune-0148df00f.1.azurestaticapps.net/?scenario=demo) | A synthetic 14 s move: a one-two beats the press, No. 10's decoy run drags a centre-back away, No. 11 scores |
| [Real match](https://red-dune-0148df00f.1.azurestaticapps.net/?scenario=real) | The same pattern found automatically in real tracking data ([Metrica Sports](https://github.com/metrica-sports/sample-data), anonymised) |

Press play, then switch **Watch as Fan / Coach / Analyst**, open the other insight tab, and hover a sentence or the
confidence badge to see the evidence behind it.

## What it finds

| Insight | Question it answers | In the demo match |
|---|---|---|
| **Space Creator** | Who created the space, without the ball? | H10's run pulls A6 3.9 m further from the receiving spot; receiving space grows 93 → 274 m² (2.9×); H10 never touches the ball |
| **Sequence Origin** | Where did this chance really begin? | The H8–H6 one-two bypasses 2 opponents, 3.6 s before the assist |

In the **real match**, Space Creator finds H10 dragging A3 11.8 m from the receiving spot as the back line drops
18.0 m, with receiving space growing 34 → 252 m² (7.5×), again without H10 touching the ball; Sequence Origin finds
the chance began with H8's pass bypassing 5 opponents, 6.5 s before the shot.

## How it works

```
tracking frames + match events      positions of all 22 players and the ball, plus passes, shots, possession
            │
            ▼
deterministic detectors (Python)    find the patterns; every insight carries numeric evidence
            │
            ▼
Microsoft Foundry agents            Explainer drafts for fan / coach / analyst, Fact-checker reviews,
(Agent Framework, gpt-4.1-mini)     code checks every claim and number, failed drafts are revised or withheld
            │
            ▼
broadcast-style replay (React)      pitch replay, cause-and-effect strip, evidence cards; hosted on Azure
```

**The AI explains; it does not decide.** The football reasoning is plain, tested code (`backend/analysis/`). The agents
only phrase findings that already carry numbers, and a grounding guard rejects any sentence that cites a field the
insight lacks or quotes a number it cannot trace. Style rules keep the three audiences genuinely different (a fan gets
at most one number; an analyst gets a measurement in every sentence), and a human reviews explanations before they
are published. See [`docs/agents.md`](docs/agents.md).

## Microsoft technology

| Technology | Used for |
|---|---|
| **Microsoft Foundry** | Hosts the `gpt-4.1-mini` deployment the agents run on |
| **Microsoft Agent Framework** | `FoundryChatClient` agents with structured (Pydantic) output: an Explainer and a Fact-checker in a revise loop |
| **Azure Static Web Apps** | Hosts the replay; redeployed from `main` by GitHub Actions on every merge |

The agents authenticate with `az login` (Azure CLI credentials), so no API keys are stored anywhere. Explanations are
generated ahead of time and committed, so the public site needs no Azure credentials and judges see exactly what was
reviewed.

## Tested on real tracking data

The detectors were built on synthetic scenarios, then run unchanged on a full real match (Metrica Sports sample game 2,
all 24 shots). Reviewing what they found exposed blind spots the synthetic data could not, and led to three rule
fixes:

- **Space Creator** credited runners after long switches of play and for space that never opened. It now requires the
  dragged defender to have been guarding the receiving spot and the space to grow at least 1.5× (9 → 2 detections,
  including a clear decoy run).
- **Sequence Origin** once credited a pass from before a turnover, and rejected every move ending in a cut-back (the
  assist goes backwards). A chance can now only begin after the attackers last won the ball, and the assist is exempt
  from the "keep moving forward" check (12 → 15, all one continuous possession).

Method, per-clip verdicts and known limits: [`docs/real-data.md`](docs/real-data.md).

## Quality

- **72 tests** (pytest): detectors, scenario realism (nobody offside, human speeds, no pass through an opponent),
  mirrored and away-team versions of the move, the grounding guard and style rules, the agent loop with a scripted
  fake model, and a re-check of every committed explanation against all current rules.
- **CI** on every push and pull request: tests, a check that committed scenario data matches the generator and
  detectors, and the frontend lint and build. CI never calls Azure.
- Work lands through small pull requests; the detection rules are documented in
  [`docs/detection-rules.md`](docs/detection-rules.md) and the data format in [`docs/data-model.md`](docs/data-model.md).

## Run it locally

```bash
# Replay
cd frontend && npm install && npm run dev        # http://localhost:5173

# Detectors and tests (Python 3.10+)
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt pytest
.venv/bin/python -m pytest backend/tests
python3 scenarios/generate_decoy_run.py
python3 backend/run_analysis.py scenarios/01_decoy_run.json

# Agent explanations (needs a Microsoft Foundry project and `az login`)
cp .env.example .env                              # set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL
.venv/bin/python -m backend.explain scenarios/01_decoy_run.insights.json

# Watch the agents work: every draft, code check, Fact-checker verdict and revision, without saving
.venv/bin/python -m backend.explain scenarios/01_decoy_run.insights.json --only SPACE_CREATOR:fan --trace --no-save
```

Useful replay links: `?scenario=real`, `?insight=1` (second insight), `?audience=coach`, `?t=10` (start time).

## Repository

```
backend/analysis/   detectors: Space Creator, Sequence Origin
backend/explain/    Foundry agents, grounding guard, audience style rules
backend/tests/      pytest suite
scenarios/          synthetic generator and data; scenarios/real/ holds the one real-match excerpt
scripts/            Metrica converter and batch analysis for real data
frontend/           Vite + React broadcast-style replay
docs/               architecture, data model, detection rules, agents, real-data results
```

## Roadmap

- **Pressing Contributor**: positioning that removes a passing option and forces a turnover ([#3](https://github.com/agbowilf/beyond-the-ball/issues/3)).
- **Near-miss scenarios and an all-detectors check** across every scenario ([#6](https://github.com/agbowilf/beyond-the-ball/issues/6)).
- **More real data**: more matches, and sharper rules for the known limits (a space figure inflated by switches of
  play; "bypassed" counting distant opponents).
- **Match Shift**: a material change in how the teams behave over a match, which needs match-length data.
- **Live explanations**: an API so new insights are explained on demand rather than ahead of time.

## Data and credits

The demo match is **synthetic**: all clubs, players and data are fictional. The real match is a short converted
excerpt of [Metrica Sports' sample data](https://github.com/metrica-sports/sample-data) (game 2), which is anonymised
and used with thanks; player labels such as H10 are ours, not shirt numbers. The rest of Metrica's data is not part of
this repository.

The code is released under the [MIT License](LICENSE). The Metrica excerpt in `scenarios/real/` is not covered by it
and remains subject to Metrica's own terms.
