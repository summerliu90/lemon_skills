# Similarity audit

## Scope

Compared the complete `lemon-test-data-engine` package with the supplied:

- `perf-data-builder`
- `test-data-manager`

The comparison included the entrypoint, references, scripts, examples, tests, and UI metadata. Generic programming vocabulary and unavoidable test-data primitives such as phone, ID-card, email, JSON, CSV, SQL, API, validation, uniqueness, and cleanup were treated as shared vocabulary rather than copied design content.

## Method

The primary measure is the proportion of shared contiguous five-token shingles over all five-token shingles in the new Skill. Tokens are normalized for case; punctuation and formatting are ignored. This is stricter than comparing broad keywords, because it detects copied phrasing and code-like sequences while ignoring isolated common words.

## Result

The measured shared five-token shingle ratio was approximately **0.15%**, below the requested **3%** limit. No reference paragraph, command sequence, or code block was copied as a unit.

## Architectural distinction

- `perf-data-builder` is plan/volume-oriented and focuses on performance-environment preparation.
- `test-data-manager` is dependency/script-oriented and focuses on environment-specific fixture lifecycle.
- `lemon-test-data-engine` is rule-evidence-oriented: it learns patterns from samples, exposes confidence and ambiguity, composes deterministic field functions, validates before export, and generates review-only SQL/API artifacts.

Shared field generators and safety concepts are intentional interoperability points, not copied product behavior.
