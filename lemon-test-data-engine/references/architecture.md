# Architecture: lemon-test-data-engine

## Modules

1. **Rule Discovery**: sample normalization, segment detection, candidate inference, confidence and questions.
2. **Rule Model**: portable field/template representation; explicit version, seed policy, constraints, and dependencies.
3. **Function Library**: deterministic primitives and domain generators with documented guarantees.
4. **Generator**: row context, sequence scopes, seeded randomness, cross-field references, scenario overrides.
5. **Validator**: syntax, type/format, uniqueness, dependency and scenario checks.
6. **Exporters**: JSON/CSV first; SQL/API/performance packages are adapters that must retain metadata and cleanup boundaries.

## Reference skill synthesis

- From `perf-data-builder`: plan-driven volume, data isolation, idempotent identifiers, batch output, sharding awareness, validation and cleanup artifacts.
- From `test-data-manager`: dependency manifests, environment-specific configuration, batch IDs, reverse-order cleanup, reusable scenario templates, and downstream data identifiers.
- New capability: samples are evidence, not authority; the skill must expose ambiguity and require confirmation before persisting a learned rule.

## Acceptance criteria

- Same template + seed produces identical output.
- Learning separates stable and changing segments and does not overclaim random/sequence semantics.
- Invalid templates fail with actionable location information.
- Generated unique fields are unique within the declared scope or generation fails.
- Output metadata makes regeneration and audit possible.
- No secret is accepted through a rule or written to an artifact.
