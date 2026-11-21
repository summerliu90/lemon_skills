# Example: Paid order has no inventory deduction

## Intake

- Category: data consistency / asynchronous workflow
- State: `TRIAGED`
- Severity/Priority: `S1 / P0`
- Expected: a successful payment eventually creates exactly one inventory ledger deduction.
- Actual: order is paid, inventory remains unchanged after 12 minutes.

## Facts

1. Payment callback succeeded at 10:03:11 (E-001).
2. Order status is `PAID` at 10:03:12 (E-002).
3. No inventory ledger row exists at 10:15:00 (E-003).
4. The event consumer was deployed at 10:00 (E-004).

## History and association

The same business flow previously failed because a duplicate idempotency key caused the consumer to skip a legitimate event. Current version differs, so the history is a candidate only. The required chain is callback → transaction → event → broker → consumer → ledger.

## Hypotheses and checks

| ID | Hypothesis | Check | Status |
|---|---|---|---|
| H-001 | Event was not emitted after commit | producer log and outbox row by order ID | candidate |
| H-002 | Event was dead-lettered or consumer failed | broker retry/dead-letter and consumer stack | candidate |
| H-003 | Consumer rejected a reused idempotency key | event ID, idempotency key and consumer ledger | candidate |
| H-004 | Ledger write succeeded but read model is stale | compare ledger and inventory projection timestamps | candidate |

## Safety boundary

Do not run a bulk repair before counting affected orders, taking a backup, proving repair idempotency and rehearsing rollback. A reconciliation queue is an acceptable temporary mitigation if it preserves an audit trail.

## Regression gates

Duplicate callback, consumer restart, message replay, partial transaction failure, delayed broker, dead-letter recovery, concurrent orders and reconciliation rerun must each result in one deterministic ledger change.
