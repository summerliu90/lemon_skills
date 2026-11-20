# Quickstart

All commands are local and produce reviewable output. They do not connect to databases or services.

## Learn a rule

```bash
python3 scripts/test_data_engine.py learn --field order_no \
  NO20261012000001 NO20261012000002 NO20261012000003
```

Review the proposed rule and its confidence before saving it.

## Generate a field

```bash
python3 scripts/test_data_engine.py generate \
  --template 'PAY{timestamp:yyyyMMddHHmmss}{random:8}' \
  --count 20 --seed 42 --format jsonl > payment.jsonl
```

## Generate related records

Create a schema file:

```json
{
  "user_id": {"template": "U{seq:6}", "unique": true},
  "order_no": "NO{date:yyyyMMdd}{seq:8}",
  "order_user_id": "{ref:user_id}",
  "status": {"template": "{choice:PAID,UNPAID}", "scenarios": {"cancelled": "CANCELLED"}}
}
```

Then inspect and generate:

```bash
python3 scripts/test_data_engine.py plan --schema schema.json
python3 scripts/test_data_engine.py records --schema schema.json --scenario cancelled --count 20 --seed 42 > orders.json
python3 scripts/test_data_engine.py verify --schema schema.json --data orders.json
```

## Export and clean up

```bash
python3 scripts/test_data_engine.py sql --schema schema.json \
  --table test_orders --batch-id tdm_20261012_001 --count 20 > setup.sql
python3 scripts/test_data_engine.py cleanup \
  --table test_orders --batch-id tdm_20261012_001 > cleanup.sql
```

Review environment, schema, and generated SQL before execution. Keep the batch ID with the test run.
