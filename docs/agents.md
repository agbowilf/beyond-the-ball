# Explanation agents

The detectors produce insights with numeric evidence. Agents turn each insight into a short explanation for a
**fan**, **coach** or **analyst**. They only rephrase what was measured: every sentence must be traceable to the
evidence, and anything that is not is rejected.

Built with **Microsoft Agent Framework** (`agent-framework-foundry`) on a model deployed in a **Microsoft Foundry**
project (`gpt-4.1-mini`, Global Standard).

## Flow

```
insight + field definitions + audience
        |
   Explainer agent  ->  headline + claims, each citing the insight fields it uses (structured output)
        |
   +----+-----------------------------+
   |                                  |
Grounding guard (code)          Fact-checker agent
every claim cites real fields;  approves, or lists claims that are
every number comes from the     unsupported, misattributed or
fields that claim cites         speculative
   |                                  |
   +----------------+-----------------+
                    |
        any problem? -> Explainer revises with the feedback (up to twice)
        still failing? -> explanation withheld, never shown
                    |
   scenarios/*.explanations.json  ->  reviewed by a person, then committed  ->  replay
```

- **Explainer** and **Fact-checker** are two `Agent`s sharing one `FoundryChatClient`, each returning a Pydantic
  model through `response_format`, so their outputs are structured, not free text.
- **Grounding guard** (`backend/explain/grounding.py`) needs no model. A number may appear in a claim only if it is a
  value of a field the claim cites (as stored, to one decimal, or rounded to a whole number), a cited confidence as a
  percentage, or part of a cited field's definition (such as the 5 s detection window). Derived numbers, such as a
  difference between two distances, are rejected even when true.
- **Audience style rules** (`backend/explain/style.py`) keep the three versions clearly different, and are checked in
  code like the guard:

  | | Fan | Coach | Analyst |
  |---|---|---|---|
  | Numbers | at most one in total | at most two per sentence | at least one per sentence |
  | Players | "North London Red's No. 10" | ids | ids |
  | Vocabulary | no jargon (marker, receiving zone, bypass, cosine...) | coaching terms that fit the insight type | technical terms |
  | Sentences | 1–2, under 20 words | exactly 3 | 3–4 |

  For every audience: headlines quote no numbers, and there is no praise or criticism (clever, precise...), no player
  positions (midfielder, defensive line...) and no raw field names or codes (markerFollowCosine, ONE_TWO). A shirt
  number must belong to a player the insight names.
- **Field definitions** (`backend/explain/glossary.py`) come from `docs/detection-rules.md`, so agents explain the
  numbers instead of guessing what they mean.

## Human review

Generated explanations are read against the evidence before they are committed. The checks catch invented or
misquoted numbers, but not every meaning error. Reviewing the first live run found two the checks missed: the
one-two's origin pass was credited with the line break, and the shot was timed from when the pass was received.
Both were fixed by sharpening the field definitions and instructions, not by editing the output.

Making the audiences distinct surfaced more of the same kind: invented locations ("near the line"), speeds
("sprinted"), positions ("midfield duo"), praise ("precise timing") and a derived figure in a headline ("over 6
metres of space"). Each was turned into a rule in the guard or style checks, so it cannot come back unnoticed.
`backend/tests/test_explanations_file.py` re-checks every committed explanation against all current rules in CI.

To regenerate one explanation without touching the others:

```bash
.venv/bin/python -m backend.explain scenarios/01_decoy_run.insights.json --only SEQUENCE_ORIGIN:coach
```

## Running

```bash
python -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cp .env.example .env    # set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL
az login
.venv/bin/python -m backend.explain scenarios/01_decoy_run.insights.json
```

Tests (`backend/tests/test_grounding.py`, `backend/tests/test_explain_agents.py`) use a scripted fake model, so CI
never calls Azure.

## Cost

Each explanation is a few small calls to `gpt-4.1-mini`, a fraction of a cent. All six explanations for the decoy
run (two insights, three audiences) take about 12 to 14 calls.

## Known limits

- Numbers written as words ("two opponents") are not checked by the guard; the fact-checker and human review cover them.
- Explanations are generated ahead of time, not live, so the deployed replay never needs Azure credentials.
