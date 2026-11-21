# Example: Search P99 regressed after release

## Intake

- Category: performance / API
- State: `VERIFYING`
- Severity/Priority: `S1 / P0`
- Baseline: P99 800 ms at 120 requests/s.
- Current: P99 6 s and timeout rate 7% at the same traffic window.

## Evidence

| ID | Evidence | Source | Level |
|---|---|---|---|
| E-001 | Regression starts eight minutes after build `2.1.0` | APM | observed |
| E-002 | Database CPU and connection wait rise together | DB monitor | observed |
| E-003 | New query plan scans the order table | EXPLAIN comparison | observed |
| E-004 | Cache hit rate is unchanged | cache dashboard | observed |
| E-005 | Container CPU limit changed in the same window | deployment manifest | observed |

## Hypotheses

1. H-001: query plan regression causes lock/connection pressure. Strong support from E-002/E-003.
2. H-002: container CPU limit causes application queueing. Supported by E-005 but does not explain the DB plan.
3. H-003: cache failure. Rejected provisionally by E-004; recheck key distribution before closure.

## Verification tasks

- Reproduce with production-like data volume and traffic shape.
- Compare plan with the previous build and capture execution time.
- Roll back only in a controlled canary and compare P99.
- Inspect connection-pool wait, lock wait and application thread queues.
- Test the proposed index in a clone; do not alter production before review.

## Decision

H-001 is `supported`, not yet `verified`; the rollback comparison is required to separate the query change from the resource-limit change.

## Remediation and regression

Short term: route a fraction of traffic to the last known-good build and cap expensive filters. Long term: fix the query/index, add plan regression checks and keep P99/timeout/connection wait as release gates. Test cold cache, high cardinality, empty filters, pagination, concurrent searches and data growth.
