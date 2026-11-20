---
name: lemon-test-data-engine
description: "Rule-driven software test data engineering: learn reusable field rules from samples, review ambiguities, generate deterministic compliant datasets, validate constraints, and export JSON/CSV/SQL artifacts. Use for API, functional, integration, and performance test-data preparation; do not invent project-specific business rules when they are not supplied."
metadata:
  short-description: Learn, define, validate, and generate rule-driven test data
---

# lemon-test-data-engine

Use this skill as a test-data factory, not as a business-domain guesser. The user owns business semantics; the engine discovers patterns, turns confirmed rules into reusable templates, and generates data from those rules.

## Operating contract

1. Identify the request mode: discover rules, define/edit rules, generate data, validate data, or prepare a performance/fixture package.
2. Establish the source of truth. Prefer explicit user rules, then confirmed learned rules, then supplied schemas/templates. Never silently infer an undocumented business constraint.
3. If samples are provided, run rule discovery and report confidence plus ambiguities before treating the result as authoritative.
4. Require or derive a seed for reproducibility. State the seed, row count, uniqueness scope, and collision policy.
5. Validate generated output against the rule, type, format, uniqueness, cross-field dependencies, and requested scenario. Fail closed when a required constraint cannot be proven.
6. For external writes or database/API execution, produce reviewable artifacts first. Never embed credentials; use environment variables and explicit environment checks.

## Modes

### Discover

Accept newline samples, JSON arrays/objects, CSV, or tabular text. Split values into stable literals and variable segments; detect dates, timestamps, padded sequences, random-looking digits, UUIDs, dictionaries, and cross-row relationships. Return a proposed rule representation, evidence, confidence, unresolved alternatives, and confirmation questions.

Use the deterministic helper when available:

```bash
python3 scripts/test_data_engine.py learn --field order_no --samples NO20261012000001 NO20261012000002
```

Do not label a changing segment random merely because it changes. Distinguish sequence, date/time, dictionary, and random candidates from their observed evidence.

### Define and generate

Rules use a small composable template language:

```text
NO{date:yyyyMMdd}{seq:6}
PAY{timestamp:yyyyMMddHHmmss}{random:8}
VIP{year}{seq:6}
```

For structured records, use JSON/YAML-like field definitions with `template`, `type`, `unique`, `depends_on`, `when`, and `scenarios` as needed. Keep templates portable and save them as artifacts rather than hidden conversational state. For very large single-field output, use `--format jsonl` so rows are emitted incrementally.

```bash
python3 scripts/test_data_engine.py generate --template 'NO{date:yyyyMMdd}{seq:6}' --count 5 --seed 42 --format json
```

For multi-field records, inspect the dependency plan first. `{ref:field}` and `depends_on` establish parent-before-child order; unknown references and cycles are errors.

```bash
python3 scripts/test_data_engine.py plan --schema schema.json
python3 scripts/test_data_engine.py records --schema schema.json --count 100 --seed 42
```

Scenario overrides are declared per field under `scenarios` (for example `normal`, `boundary`, `expired`, or `invalid`). SQL export is review-only output and always adds a batch identifier; it does not connect to a database.

```bash
python3 scripts/test_data_engine.py records --schema schema.json --scenario expired --count 20
python3 scripts/test_data_engine.py sql --schema schema.json --table test_user --batch-id tdm_20261012_001 --count 20
```

Verify a saved JSON array before using it, and generate cleanup SQL separately. Cleanup is batch-scoped and is never executed by the helper.

```bash
python3 scripts/test_data_engine.py verify --schema schema.json --data generated.json
python3 scripts/test_data_engine.py cleanup --table test_user --batch-id tdm_20261012_001
```

For API-created data, generate a reviewable runner. It reads `API_BASE_URL` and `API_TOKEN` from the environment, adds the batch ID, retries transient failures, and never runs automatically:

```bash
python3 scripts/test_data_engine.py api-template \
  --data orders.json --endpoint /api/orders \
  --method POST --batch-id tdm_20261012_001 --count 20 > load_orders.py
```

For performance preparation, calculate the plan before generating rows. The command reports total, hot/cold split, per-slave allocation, and an isolation tag. Ratios and environment assumptions must be reviewed against the real workload.

```bash
python3 scripts/test_data_engine.py perf-plan --plan-id orders \
  --concurrency 6000 --minutes 23 --interface-type write --slaves 4
```

Supported primitives in the bundled engine: literals, `date`, `timestamp`, `year`, `seq`, `random`, `uuid`, and `choice`. Complex domain generators (phone, ID card, address, money, etc.) should be added as explicit functions with tests and documented validity guarantees.

The bundled `phone`, `idcard`, `email`, `name`, `address`, and `money` functions are synthetic. `idcard` includes a valid checksum but must never be treated as real personal data.

### Validate and export

Validate samples or generated files before claiming compliance. Report errors by row/field and separate format failures, uniqueness failures, dependency failures, and insufficient evidence. Export only after validation, with metadata including template, seed, count, generation time, and validation result.

For performance data, combine this skill with the reference patterns: calculate volume from the test plan, partition hot/cold data, use batch generation, stable identifiers, environment tags, and cleanup/verification artifacts. Do not copy fixed formulas without confirming the workload.

## Safety and quality boundaries

- Never put passwords, tokens, production URLs, or real personal data in generated files or examples.
- SQL table and field identifiers are restricted to simple names; never bypass this guard with concatenated SQL.
- Synthetic personal data must be clearly marked; preserve format validity without pretending it belongs to a real person.
- Do not execute SQL, API calls, destructive cleanup, or production writes without an explicit user request and a confirmed target environment.
- For dependent records, produce a dependency graph and generate parents before children; cleanup is reverse topological order.
- Prefer deterministic generation for tests. Use randomness only when requested, seeded, and accompanied by collision handling.

## Supporting resources

- Read `references/architecture.md` for the design rationale, module boundaries, and acceptance criteria.
- Read `references/rule-language.md` when defining or reviewing templates.
- Use `scripts/test_data_engine.py` for deterministic discovery and generation.
