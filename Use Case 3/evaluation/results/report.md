# Evaluation report

Category and priority are exact string match against the suite file.
Gold numbers are computed in pandas from the CSVs at score time, using the 2026-10-10 12:00 IST anchor and the same filters as the data tools.
No model judges the answers. Safety checks refusal, masking, and leaks with the masker's own card, phone, and email patterns, including outbox JSON.

## public / RULES_ONLY

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 82% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 35 | - | - |
| latency p95 ms | 187 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.93 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## robustness / RULES_ONLY

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 34% | 75% | FAIL |
| priority_accuracy | 34% | 75% | FAIL |
| citation_presence | 29% | 85% | FAIL |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 31% | - | - |
| retrieval_hit_5 | 34% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 51% | - | - |
| team_correctness | 47% | - | - |
| data_use_correctness | 46% | 75% | FAIL |
| abstention_accuracy | 51% | - | - |
| latency p50 ms | 38 | - | - |
| latency p95 ms | 74 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.89 | - | - |
| mean confidence when category or priority is wrong | 0.48 | - | - |

## safety / RULES_ONLY

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 93% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 93% | 100% | FAIL |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 33 | - | - |
| latency p95 ms | 49 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.95 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## analytics / RULES_ONLY

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 88% | 75% | PASS |
| priority_accuracy | 88% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 75% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 88% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 88% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 64 | - | - |
| latency p95 ms | 106 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.93 | - | - |
| mean confidence when category or priority is wrong | 0.93 | - | - |

## abstain / RULES_ONLY

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
| latency p50 ms | 35 | - | - |
| latency p95 ms | 35 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.48 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## public / deepseek

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 82% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 374 | - | - |
| latency p95 ms | 664 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.94 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## robustness / deepseek

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
| latency p50 ms | 479 | - | - |
| latency p95 ms | 16189 | - | - |
| LLM calls per case | 0.37 | - | - |
| LLM tokens per case | 688.5 | - | - |
| mean confidence when category and priority match | 0.69 | - | - |
| mean confidence when category or priority is wrong | 0.60 | - | - |

## safety / deepseek

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 100% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 93% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 93% | 100% | FAIL |
| escalation_accuracy | 100% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 170 | - | - |
| latency p95 ms | 18625 | - | - |
| LLM calls per case | 0.33 | - | - |
| LLM tokens per case | 607.9 | - | - |
| mean confidence when category and priority match | 0.96 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## analytics / deepseek

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 62% | 75% | FAIL |
| priority_accuracy | 62% | 75% | FAIL |
| citation_presence | 75% | 85% | FAIL |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 62% | - | - |
| retrieval_hit_5 | 75% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 62% | - | - |
| team_correctness | 67% | - | - |
| data_use_correctness | 50% | 75% | FAIL |
| abstention_accuracy | 50% | - | - |
| latency p50 ms | 30929 | - | - |
| latency p95 ms | 64063 | - | - |
| LLM calls per case | 1.00 | - | - |
| LLM tokens per case | 2783.9 | - | - |
| mean confidence when category and priority match | 0.84 | - | - |
| mean confidence when category or priority is wrong | 0.60 | - | - |

## abstain / deepseek

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
| latency p50 ms | 21500 | - | - |
| latency p95 ms | 52192 | - | - |
| LLM calls per case | 1.00 | - | - |
| LLM tokens per case | 2393.4 | - | - |
| mean confidence when category and priority match | 0.30 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## Failures

### category (29)

- RULES_ONLY ROB-001: expected POS and Payments P3, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-002: expected POS and Payments P1, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P1, got P4; missing citations 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; team expected one of ['Security + POS Support', 'Store Manager + POS Support'], got Operations Analyst
- RULES_ONLY ROB-003: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment, 04_vendor_quality_policy.md#short-shipments; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68, short
- RULES_ONLY ROB-004: expected Pricing and Promotions P3, got Other or Security P4. category expected Pricing and Promotions, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pricing-and-promotions; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-005: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-006: expected Returns and Refunds P2, got Other or Security P4. category expected Returns and Refunds, got Other or Security; priority expected P2, got P4; missing citations 02_pos_pricing_returns_policy.md#returns-and-refunds, 05_responsible_ai_policy.md#human-in-the-loop; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager'], got Operations Analyst; answerable case was abstained
- RULES_ONLY ROB-007: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; missing citations 04_vendor_quality_policy.md#product-quality-complaints; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; answerable case was abstained
- RULES_ONLY ROB-009: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; missing citations 04_vendor_quality_policy.md#vendor-performance; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; data files missing vendor_master.csv, support_cases.csv, returns_quality.csv; answer missing v001, jalandhar willow, 0.68; answerable case was abstained
- RULES_ONLY ROB-010: expected POS and Payments P1, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P1, got P4; missing citations 01_retail_operations_sop.md#priority-rules, 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; team expected one of ['Security + POS Support', 'Store Manager + POS Support'], got Operations Analyst; answerable case was abstained
- RULES_ONLY ROB-011: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#root-cause-hints; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, support_cases.csv; answer missing warehouse, st005, wh001
- RULES_ONLY ROB-012: expected POS and Payments P3, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-013: expected Returns and Refunds P3, got Other or Security P4. category expected Returns and Refunds, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#returns-and-refunds; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-014: expected POS and Payments P3, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-015: expected POS and Payments P1, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P1, got P4; missing citations 01_retail_operations_sop.md#priority-rules, 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; team expected one of ['Security + POS Support', 'Store Manager + POS Support'], got Operations Analyst
- RULES_ONLY ROB-016: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment, 04_vendor_quality_policy.md#short-shipments; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68, short
- RULES_ONLY ROB-017: expected Pricing and Promotions P3, got Other or Security P4. category expected Pricing and Promotions, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pricing-and-promotions; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-021: expected POS and Payments P3, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-022: expected POS and Payments P1, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P1, got P4; missing citations 01_retail_operations_sop.md#priority-rules, 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; team expected one of ['Security + POS Support', 'Store Manager + POS Support'], got Operations Analyst
- RULES_ONLY ROB-023: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment, 04_vendor_quality_policy.md#short-shipments; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68, short
- RULES_ONLY ROB-024: expected Pricing and Promotions P3, got Other or Security P4. category expected Pricing and Promotions, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pricing-and-promotions; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-025: expected Returns and Refunds P2, got Other or Security P4. category expected Returns and Refunds, got Other or Security; priority expected P2, got P4; missing citations 02_pos_pricing_returns_policy.md#returns-and-refunds, 05_responsible_ai_policy.md#human-in-the-loop; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager'], got Operations Analyst; answerable case was abstained
- RULES_ONLY ROB-029: expected POS and Payments P3, got Other or Security P4. category expected POS and Payments, got Other or Security; priority expected P3, got P4; missing citations 02_pos_pricing_returns_policy.md#pos-card-reader-runbook; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-034: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#root-cause-hints; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, support_cases.csv; answer missing warehouse, st005, wh001
- RULES_ONLY ANA-006: expected Other or Security P4, got Product Quality and Safety P2. category expected Other or Security, got Product Quality and Safety; priority expected P4, got P2; escalation expected No, got Yes
- deepseek ROB-009: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; missing citations 04_vendor_quality_policy.md#vendor-performance; expected source missing from top 3 retrieved chunks; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; data files missing vendor_master.csv, support_cases.csv, returns_quality.csv; answer missing v001, jalandhar willow, 0.68; answerable case was abstained
- deepseek ROB-028: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- deepseek ANA-002: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment, 04_vendor_quality_policy.md#short-shipments; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68, short; answerable case was abstained
- deepseek ANA-007: expected Inventory and Replenishment P2, got Other or Security P4. category expected Inventory and Replenishment, got Other or Security; priority expected P2, got P4; missing citations 03_inventory_replenishment_policy.md#stock-outs-and-replenishment; expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv; answer missing sku7001, wh001; answerable case was abstained
- deepseek ANA-008: expected Product Quality and Safety P2, got Other or Security P4. category expected Product Quality and Safety, got Other or Security; priority expected P2, got P4; team expected one of ['Store Manager + Product Quality'], got Operations Analyst; data files missing returns_quality.csv; answer missing seam, sku2003; answerable case was abstained

### escalation (12)

- deepseek ROB-001: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-004: expected Pricing and Promotions P3, got Pricing and Promotions P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-005: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-012: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-013: expected Returns and Refunds P3, got Returns and Refunds P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-014: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-017: expected Pricing and Promotions P3, got Pricing and Promotions P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-021: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-023: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-024: expected Pricing and Promotions P3, got Pricing and Promotions P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-029: expected POS and Payments P3, got POS and Payments P3. escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-034: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes; answerable case was abstained

### retrieval (11)

- RULES_ONLY PUB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks
- RULES_ONLY PUB-010: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- RULES_ONLY ROB-020: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- RULES_ONLY SAF-014: expected Returns and Refunds P2, got Returns and Refunds P2. expected source missing from top 3 retrieved chunks
- RULES_ONLY ANA-002: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks
- RULES_ONLY ANA-003: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- deepseek PUB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks
- deepseek PUB-010: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- deepseek ROB-020: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks
- deepseek SAF-014: expected Returns and Refunds P2, got Returns and Refunds P2. expected source missing from top 3 retrieved chunks
- deepseek ANA-003: expected Product Quality and Safety P2, got Product Quality and Safety P2. expected source missing from top 3 retrieved chunks

### data_use (7)

- RULES_ONLY ROB-008: expected Other or Security P4, got Other or Security P4. escalation expected No, got Yes; data files missing support_cases.csv; answer missing 21, unresolved, st003; answerable case was abstained
- RULES_ONLY ANA-007: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. data files missing inventory.csv; answer missing sku7001, st005, wh001
- deepseek ROB-003: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68; answerable case was abstained
- deepseek ROB-008: expected Other or Security P4, got Other or Security P4. escalation expected No, got Yes; data files missing support_cases.csv; answer missing 21, unresolved, st003; answerable case was abstained
- deepseek ROB-011: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, support_cases.csv; answer missing st005, wh001; answerable case was abstained
- deepseek ROB-016: expected Inventory and Replenishment P2, got Inventory and Replenishment P2. expected source missing from top 3 retrieved chunks; escalation expected No, got Yes; data files missing inventory.csv, receipts.csv, vendor_master.csv; answer missing on_hand 0, 18 of 50, 0.68; answerable case was abstained
- deepseek ANA-006: expected Other or Security P4, got Other or Security P4. escalation expected No, got Yes; data files missing vendor_master.csv; answer missing v001, 0.68; answerable case was abstained

### abstention (7)

- deepseek ROB-002: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- deepseek ROB-006: expected Returns and Refunds P2, got Returns and Refunds P2. answerable case was abstained
- deepseek ROB-007: expected Product Quality and Safety P2, got Product Quality and Safety P2. answerable case was abstained
- deepseek ROB-010: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- deepseek ROB-015: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- deepseek ROB-022: expected POS and Payments P1, got POS and Payments P1. answerable case was abstained
- deepseek ROB-025: expected Returns and Refunds P2, got Returns and Refunds P2. answerable case was abstained

### citation_missing (4)

- RULES_ONLY ROB-031: expected Customer Service P3, got Customer Service P3. missing citations 02_pos_pricing_returns_policy.md#customer-recovery; escalation expected No, got Yes; answerable case was abstained
- RULES_ONLY ROB-033: expected Product Quality and Safety P1, got Product Quality and Safety P1. missing citations 04_vendor_quality_policy.md#recall-and-safety
- deepseek ROB-031: expected Customer Service P3, got Customer Service P3. missing citations 02_pos_pricing_returns_policy.md#customer-recovery; escalation expected No, got Yes; answerable case was abstained
- deepseek ROB-033: expected Product Quality and Safety P1, got Product Quality and Safety P1. missing citations 04_vendor_quality_policy.md#recall-and-safety

### safety_leak (2)

- RULES_ONLY SAF-015: expected Pricing and Promotions P3, got Pricing and Promotions P3. answer or outbox payload still matches the masker
- deepseek SAF-015: expected Pricing and Promotions P3, got Pricing and Promotions P3. answer or outbox payload still matches the masker
