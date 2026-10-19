# Architecture

```
scenarios/generate_*.py  ->  scenarios/*.json               (frames + events)
backend/analysis/        ->  scenarios/*.insights.json      (insights with numeric evidence)
backend/explain/         ->  scenarios/*.explanations.json  (checked explanations, per audience)
frontend/                ->  pitch replay, insight tabs, evidence and explanations
```

See `docs/agents.md` for how the Microsoft Foundry agents write and check explanations.

## Principles

1. **Separation of data and analysis.** Generators only emit positions and events. Detectors never read scenario
   metadata or labels, so a detection is a real calculation, not a hard-coded answer.
2. **Deterministic first, AI second.** Football reasoning is code with numeric evidence. The AI layer only turns
   structured findings into language and may not add tactical claims.
3. **Scripted scenarios, not a full simulator.** Short sequences designed to contain specific off-ball situations,
   plus background players with small seeded noise.
4. **Azure last.** Prove the detectors locally, then wrap Foundry/Azure around the structured insights.
