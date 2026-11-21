# Example: Assistant loses a confirmed constraint after several turns

## Intake

- Category: AI / context management
- State: `DIAGNOSING`
- Severity/Priority: `S2 / P1`
- Expected: the assistant follows the confirmed city and date constraints.
- Actual: the sixth-turn answer proposes a different city without explaining a change.

## Evidence ledger

| ID | Observation | Source | Level |
|---|---|---|---|
| E-001 | The constraint appears in the second user message | TestPilot transcript | observed |
| E-002 | The sixth response violates the city constraint | assertion result | observed |
| E-003 | Prompt template changed between builds | release diff | observed |
| E-004 | Context length and truncation marker are missing | gateway log gap | missing |

## Historical review

Two historical cases match the symptom. One was caused by context truncation; the other by a retrieval result overwriting the user constraint. Neither can be reused until the current prompt, context assembly and retrieval trace are compared.

## Hypotheses

| ID | Claim | Prediction | Status |
|---|---|---|---|
| H-001 | Old turns are truncated before generation | token count reaches limit and the second message is absent | candidate |
| H-002 | Retrieval context contains a conflicting city and is treated as authoritative | retrieved chunk includes a different city and prompt gives it priority | candidate |
| H-003 | Prompt template regression changed constraint priority | build diff shows instruction or message-order change | supported |

## Verification

1. Replay identical transcript on old and new builds; preserve model, parameters and tools.
2. Capture assembled messages, token counts and truncation decisions.
3. Capture retrieval chunks and their ranking.
4. Disable retrieval once and repeat; compare the answer.
5. Run the prompt contract suite for multi-turn constraint retention.

## Decision

The prompt change is supported by evidence, but root cause is not confirmed until assembled context is inspected. Do not label the issue as model hallucination.

## Fix and regression

- Add a machine-readable constraint ledger before generation.
- Mark user-confirmed constraints separately from retrieved context.
- Add tests for context truncation, conflicting retrieval, model fallback and tool retry.
- Monitor constraint-violation rate by model and prompt version.
