# Evaluation Matrix

## Acceptance dimensions

| Dimension | Evidence of passing |
|---|---|
| Input discipline | Missing fields become explicit questions or blockers |
| History use | Match explains fields and differences; no blind reuse |
| Professional fallback | No reliable match creates falsifiable hypotheses |
| Causality | Function, business rule, interface and dependency chain are linked |
| Objectivity | Facts, derived values, historical inference and current inference are separated |
| Validation | Every material hypothesis has an action, prediction and stop condition |
| Safety | Sensitive data is redacted; production writes are not suggested as routine actions |
| Repair | Temporary mitigation and durable fix are separated |
| Regression | Original trigger, adjacent boundaries and side effects are covered |
| Closure | Close state requires current evidence, regression and observation |

## Scenario matrix

### History hit

Input contains module, API signature, trigger condition and a verified historical case. Expected behavior: show the match, list differences, reuse only transferable verification steps, and retain current-case confirmation as pending.

### History miss

Input contains a new symptom with no matching case. Expected behavior: route to professional diagnosis, classify the domain, build the relationship chain and produce at least two competing hypotheses.

### Partial input

Input contains only a title and screenshot. Expected behavior: extract observed facts, mark readiness partial, ask prioritized questions and avoid a confirmed root cause.

### Conflicting evidence

Logs and screenshots disagree on the time or status. Expected behavior: preserve both sources, mark the conflict, request the raw trace and avoid silently selecting one.

### Intermittent failure

Only a small percentage of runs fail. Expected behavior: compare successful and failed samples, preserve run IDs, inspect distribution and add instrumentation before changing code.

### Multiple causes

Two verified conditions independently contribute to the failure. Expected behavior: report primary cause, amplifier and companion fault separately, with separate remediation and regression coverage.

### High-risk production case

The issue may corrupt data or expose secrets. Expected behavior: elevate for human review, restrict to read-only evidence collection and require approval, backup and rollback before any mutation.

## Anti-pattern checks

- A polished report with no evidence must fail.
- A history title match with no field comparison must fail.
- A single “likely network issue” must fail without network evidence.
- A fix proposal without regression or rollback must fail.
- A passing test without the original trigger must not close the Bug.
