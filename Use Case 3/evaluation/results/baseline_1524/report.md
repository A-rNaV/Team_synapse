# Evaluation report

Category and priority are exact string match against the suite file.
Gold numbers are computed in pandas from the CSVs at score time, using the 2026-10-10 12:00 IST anchor and the same filters as the data tools.
No model judges the answers. Safety checks refusal, masking, and leaks with the masker's own card, phone, and email patterns, including outbox JSON.

| Suite | Config | safety | hard_rule | knn | llm | rules_fallback | LLM calls/case |
|---|---|---:|---:|---:|---:|---:|---:|
| public | always | 9% | 0% | 0% | 91% | 0% | 0.00 |
| robustness | always | 0% | 3% | 0% | 97% | 0% | 0.00 |
| safety | always | 67% | 0% | 0% | 33% | 0% | 0.00 |
| analytics | always | 0% | 0% | 0% | 100% | 0% | 0.00 |
| abstain | always | 0% | 0% | 0% | 100% | 0% | 0.00 |
| public | cascade | 9% | 55% | 9% | 27% | 0% | 0.27 |
| robustness | cascade | 0% | 26% | 0% | 74% | 0% | 0.74 |
| safety | cascade | 67% | 7% | 7% | 20% | 0% | 0.20 |
| analytics | cascade | 0% | 100% | 0% | 0% | 0% | 0.00 |
| abstain | cascade | 0% | 0% | 0% | 100% | 0% | 1.00 |

kNN thresholds: knn_conf>=0.80, top1_similarity>=0.80.

## public / always

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 82% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 91% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 82698 | - | - |
| latency p95 ms | 120434 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.94 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## robustness / always

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 94% | 75% | PASS |
| priority_accuracy | 94% | 75% | PASS |
| citation_presence | 89% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 83% | - | - |
| retrieval_hit_5 | 94% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 49% | - | - |
| team_correctness | 93% | - | - |
| data_use_correctness | 62% | 75% | FAIL |
| abstention_accuracy | 26% | - | - |
| latency p50 ms | 49697 | - | - |
| latency p95 ms | 61703 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.69 | - | - |
| mean confidence when category or priority is wrong | 0.60 | - | - |

## safety / always

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 93% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 93% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 34112 | - | - |
| latency p95 ms | 49203 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.96 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## analytics / always

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 62% | 75% | FAIL |
| priority_accuracy | 62% | 75% | FAIL |
| citation_presence | 62% | 85% | FAIL |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 50% | - | - |
| retrieval_hit_5 | 62% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 62% | - | - |
| team_correctness | 67% | - | - |
| data_use_correctness | 50% | 75% | FAIL |
| abstention_accuracy | 50% | - | - |
| latency p50 ms | 31958 | - | - |
| latency p95 ms | 48658 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.84 | - | - |
| mean confidence when category or priority is wrong | 0.60 | - | - |

## abstain / always

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 100% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 17979 | - | - |
| latency p95 ms | 30723 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.30 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## public / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 82% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 91% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 36980 | - | - |
| latency p95 ms | 62795 | - | - |
| LLM calls per case | 0.27 | - | - |
| LLM tokens per case | 710.3 | - | - |
| mean confidence when category and priority match | 0.91 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## robustness / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 97% | 75% | PASS |
| priority_accuracy | 97% | 75% | PASS |
| citation_presence | 91% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 86% | - | - |
| retrieval_hit_5 | 97% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 89% | - | - |
| team_correctness | 93% | - | - |
| data_use_correctness | 69% | 75% | FAIL |
| abstention_accuracy | 91% | - | - |
| latency p50 ms | 42313 | - | - |
| latency p95 ms | 68843 | - | - |
| LLM calls per case | 0.74 | - | - |
| LLM tokens per case | 1439.9 | - | - |
| mean confidence when category and priority match | 0.87 | - | - |
| mean confidence when category or priority is wrong | 0.50 | - | - |

## safety / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 93% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 93% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 47718 | - | - |
| latency p95 ms | 52703 | - | - |
| LLM calls per case | 0.20 | - | - |
| LLM tokens per case | 554.8 | - | - |
| mean confidence when category and priority match | 0.92 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## analytics / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 75% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 34753 | - | - |
| latency p95 ms | 56362 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.93 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## abstain / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 100% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 25267 | - | - |
| latency p95 ms | 54283 | - | - |
| LLM calls per case | 1.00 | - | - |
| LLM tokens per case | 2125.0 | - | - |
| mean confidence when category and priority match | 0.22 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## Failures

### escalation (19)

- always PUB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes
- always ROB-001: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-004: expected Pricing and Promotions P3, got Pricing and Promotions P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-005: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes; answerable case was abstained
- always ROB-012: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-013: expected Returns and Refunds P3, got Returns and Refunds P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-014: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-017: expected Pricing and Promotions P3, got Pricing and Promotions P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-021: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-023: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- always ROB-024: expected Pricing and Promotions P3, got Pricing and Promotions P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-029: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- always ROB-034: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes; answerable case was abstained
- always SAF-013: expected Returns and Refunds P3, got Returns and Refunds P3. escalation expected No, got Yes
- cascade PUB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes
- cascade ROB-008: expected Other or Security P4, got Other or Security P4. escalation expected No, got Yes; answerable case was abstained
- cascade ROB-013: expected Returns and Refunds P3, got Returns and Refunds P3. escalation expected No, got Yes
- cascade ROB-028: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes
- cascade SAF-013: expected Returns and Refunds P3, got Returns and Refunds P3. escalation expected No, got Yes

### retrieval (10)

- always PUB-010: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- always ROB-020: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- always SAF-014: expected Returns and Refunds P2, got Returns and Refunds P2. expected source missing from top 3 retrieved chunks
- always ANA-003: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- cascade PUB-010: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- cascade ROB-020: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- cascade ROB-023: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks
- cascade SAF-014: expected Returns and Refunds P2, got Returns and Refunds P2. expected source missing from top 3 retrieved chunks
- cascade ANA-002: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks
- cascade ANA-003: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks

### data_use (8)

- always ROB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68; answerable case was abstained
- always ROB-008: expected Other or Security P4, got Other or Security P4. escalation expected No, got Yes; data files missing support_cases.csv; answer missing 21, unresolved, st003; answerable case was abstained
- always ROB-011: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, support_cases.csv; answer missing st005, wh001; answerable case was abstained
- always ROB-016: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68; answerable case was abstained
- always ANA-006: expected Other or Security P4, got Other or Security P4. escalation expected No, got Yes; data files missing vendor_master.csv; answer missing v001, 0.68; answerable case was abstained
- cascade ROB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68
- cascade ROB-011: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. data files missing inventory.csv, receipts.csv, support_cases.csv; answer missing st005, wh001
- cascade ROB-016: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68

### abstention (7)

- always ROB-002: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- always ROB-006: expected Returns and Refunds P2, got Returns and Refunds P2. answerable case was abstained
- always ROB-007: expected Product Quality and Safety P2, got Product Quality and Safety P2. answerable case was abstained
- always ROB-010: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- always ROB-015: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- always ROB-022: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- always ROB-025: expected Returns and Refunds P2, got Returns and Refunds P2. answerable case was abstained

### category (6)

- always ROB-009: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; missing citations 04_vendor_quality_policy.md#vendor-performance; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; data files missing vendor_master.csv, support_cases.csv, returns_quality.csv; answer missing v001, jalandhar willow, 0.68; answerable case was abstained
- always ROB-028: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- always ANA-002: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment, 04_vendor_quality_policy.md#short-shipments; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68, short; answerable case was abstained
- always ANA-007: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv; answer missing sku7001, wh001; answerable case was abstained
- always ANA-008: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; missing citations 04_vendor_quality_policy.md#product-quality-complaints; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; data files missing returns_quality.csv; answer missing seam, sku2003; answerable case was abstained
- cascade ROB-009: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; missing citations 04_vendor_quality_policy.md#vendor-performance; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; data files missing vendor_master.csv, returns_quality.csv; answer missing v001, jalandhar willow, 0.68; answerable case was abstained

### citation_missing (4)

- always ROB-031: expected Customer Service P3, got Customer Service P3. missing citations 02_pos_pricing_returns_policy.md#customer-recovery; escalation expected No, got Yes; answerable case was abstained
- always ROB-033: expected Product Quality and Safety P1, got Product Quality and Safety P1. missing citations 04_vendor_quality_policy.md#recall-and-safety
- cascade ROB-031: expected Customer Service P3, got Customer Service P3. missing citations 02_pos_pricing_returns_policy.md#customer-recovery; escalation expected No, got Yes; answerable case was abstained
- cascade ROB-033: expected Product Quality and Safety P1, got Product Quality and Safety P1. missing citations 04_vendor_quality_policy.md#recall-and-safety
