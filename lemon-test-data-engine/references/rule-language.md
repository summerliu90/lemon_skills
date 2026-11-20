# Rule language

Template text is a sequence of literal text and `{function:argument}` tokens.

| Token | Meaning | Example |
|---|---|---|
| `date` | current/reference date | `{date:yyyyMMdd}` |
| `timestamp` | reference timestamp | `{timestamp:yyyyMMddHHmmss}` |
| `year` | four-digit year | `{year}` |
| `seq` | zero-padded row sequence | `{seq:6}` |
| `random` | seeded numeric value | `{random:8}` |
| `uuid` | deterministic UUID from seed/row | `{uuid}` |
| `choice` | seeded selection from comma-separated values | `{choice:PAID,UNPAID}` |
| `phone` | synthetic mainland-style mobile number | `{phone}` |
| `idcard` | synthetic checksum-valid 18-digit ID; pass a prior city field for a matching administrative code | `{idcard:city}` |
| `email` | synthetic non-routable email | `{email}` |
| `name` | clearly synthetic Chinese name | `{name}` |
| `address` | clearly synthetic address | `{address}` |
| `money` | seeded two-decimal amount | `{money}` |
| `ref` | value from an earlier field in the same record | `{ref:user_id}` |

Dates use `yyyy`, `MM`, `dd`, `HH`, `mm`, `ss`. A sequence starts at 1 unless configured otherwise. Random values are generated with a local seeded generator, never a global process RNG.
