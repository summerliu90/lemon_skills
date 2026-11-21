# Example: Payment succeeded but inventory remained unchanged

## 1. Intake decision

- State: `HISTORY_REVIEW`
- Severity: `S1`
- Priority: `P0`
- Readiness: `PARTIAL`
- Blocking input: consumer log for the payment event and inventory record timeline.

## 2. Observed facts

1. Payment callback returned success for order `O-1001` (E-001, payment log).
2. Order status became `PAID` (E-002, order API response).
3. Inventory quantity was unchanged 12 minutes later (E-003, read-only query).
4. The issue was observed only after version `order-3.8.0` deployment (E-004, release record).

## 3. Relationship chain

```text
payment callback
  -> order transaction
  -> inventory event
  -> inventory consumer
  -> stock ledger
```

The chain is currently broken between event production and consumer acknowledgement; this is a diagnostic gap, not yet the root cause.

## 4. Historical review

`HIST-014` matches the same business flow and event type, but its verified cause was duplicate consumer delivery under `inventory-2.4.1`. The current deployment and failure window differ, so the historical cause is a candidate only. Recheck idempotency and consumer logs.

## 5. Hypotheses

| ID | Claim | Supporting evidence | Counter evidence | State |
|---|---|---|---|---|
| H-001 | Event was not published after the order transaction | E-001, E-002, E-003 | no producer log yet | candidate |
| H-002 | Event was published but consumer failed or entered dead letter | E-003, E-004 | consumer evidence missing | candidate |
| H-003 | Consumer applied stock change but read model is stale | E-003 | no ledger query yet | candidate |
| H-004 | Duplicate delivery was rejected by an incorrect idempotency key | historical match, E-004 | no duplicate evidence | candidate |

## 6. Verification tasks

1. Query producer logs by order ID and event ID. Expected: one committed event after payment commit.
2. Query broker delivery, retry and dead-letter records. Expected: a failed or unacknowledged delivery supports H-002.
3. Query stock ledger and read model with timestamps. Expected: ledger change plus stale read model supports H-003.
4. Replay the event in a non-production environment with the same idempotency key. Expected: one stock change and deterministic acknowledgement.

## 7. Current decision

Root cause is **not confirmed**. The current evidence supports an asynchronous consistency break but cannot distinguish publication, consumption and read-model delay.

## 8. Remediation boundaries

- Temporary: stop automatic payment-to-stock release for affected orders and create a monitored reconciliation queue.
- Do not run a bulk repair until backup, idempotency and dry-run counts are reviewed.
- Long term: expose event lifecycle metrics and add an invariant check between paid orders and stock ledger entries.

## 9. Regression gates

- Duplicate callback does not decrement inventory twice.
- Consumer restart resumes from the correct offset.
- Dead-letter replay is idempotent.
- Payment success with inventory failure creates an observable compensation task.
- Reconciliation reports the exact order and stock delta.
