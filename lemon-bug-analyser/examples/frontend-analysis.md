# Example: Order page is blank only on Safari

## Intake

- Category: frontend / compatibility
- State: `HISTORY_REVIEW`
- Severity/Priority: `S1 / P1`
- Expected: loading state followed by the order list.
- Actual: blank page; Safari Console reports a runtime exception.

## Facts and scope

1. Chrome 128 renders the page successfully (E-001).
2. Safari 17.6 fails on the same account and data (E-002).
3. The order API returns HTTP 200 in both browsers (E-003).
4. The failure began with web build `5.4.2` (E-004).
5. The response contains a nullable field introduced by API version `v2` (E-005).

## Relationship chain

```text
route -> data fetch -> response normalization -> state store -> component render
```

Network success does not prove render safety. The next observation must identify the first broken link.

## Hypotheses

| ID | Claim | Check | Status |
|---|---|---|---|
| H-001 | Safari lacks a feature used by the bundle | compare Console stack and transpiled output | candidate |
| H-002 | Nullable API field is dereferenced by the normalizer | replay response with field null and inspect stack | supported |
| H-003 | Cached stale chunk is mixed with the new API contract | clear cache and inspect asset hashes | candidate |

## Verification plan

- Use the exact response fixture in Chrome and Safari.
- Add a temporary boundary log before normalization and before render.
- Compare source-map positions and bundle compatibility target.
- Repeat after cache and Service Worker reset.

## Decision and remediation

The API contract change is the strongest current lead, not a confirmed root cause. Guard the nullable field only after confirming the contract; add schema validation and a visible error state. Release with a rollback switch and observe Safari error rate for 24 hours.

## Regression gates

Safari/Chrome/Firefox, mobile Safari, empty response, null field, malformed response, expired session, stale cache, slow network and API 500.
