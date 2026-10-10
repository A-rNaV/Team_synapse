# Evaluation report

Category and priority are exact string match against the suite file.
Gold numbers are computed in pandas from the CSVs at score time, using the 2026-10-10 12:00 IST anchor and the same filters as the data tools.
No model judges the answers. Safety checks refusal, masking, and leaks with the masker's own card, phone, and email patterns, including outbox JSON.

| Suite | Config | safety | hard_rule | knn | llm | rules_fallback | LLM calls/case |
|---|---|---:|---:|---:|---:|---:|---:|
| public | cascade | 9% | 55% | 9% | 0% | 0% | 0.00 |
| robustness | cascade | 0% | 37% | 3% | 54% | 0% | 0.46 |
| safety | cascade | 67% | 7% | 13% | 0% | 0% | 0.00 |
| analytics | cascade | 0% | 100% | 0% | 0% | 0% | 0.00 |
| abstain | cascade | 0% | 0% | 0% | 100% | 0% | 1.00 |

kNN thresholds: knn_conf>=0.50, top1_similarity>=0.70.

## public / cascade

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
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 20591 | - | - |
| latency p95 ms | 26732 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.93 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## robustness / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 100% | 75% | PASS |
| priority_accuracy | 97% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 100% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 97% | - | - |
| team_correctness | 100% | - | - |
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 21651 | - | - |
| latency p95 ms | 30673 | - | - |
| LLM calls per case | 0.46 | - | - |
| LLM tokens per case | 481.0 | - | - |
| mean confidence when category and priority match | 0.90 | - | - |
| mean confidence when category or priority is wrong | 0.71 | - | - |

## safety / cascade

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
| latency p50 ms | 19583 | - | - |
| latency p95 ms | 26044 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.95 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## analytics / cascade

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
| data_use_correctness | 100% | 75% | PASS |
| abstention_accuracy | 100% | - | - |
| latency p50 ms | 27612 | - | - |
| latency p95 ms | 30108 | - | - |
| LLM calls per case | 0.00 | - | - |
| LLM tokens per case | 0.0 | - | - |
| mean confidence when category and priority match | 0.93 | - | - |
| mean confidence when category or priority is wrong | n/a | - | - |

## abstain / cascade

| Metric | Result | Target | Status |
|---|---:|---:|---|
| category_accuracy | 80% | 75% | PASS |
| priority_accuracy | 80% | 75% | PASS |
| citation_presence | 100% | 85% | PASS |
| citation_validity | 100% | 85% | PASS |
| retrieval_hit_3 | 100% | - | - |
| retrieval_hit_5 | 100% | - | - |
| safety_pass_rate | 100% | 100% | PASS |
| escalation_accuracy | 40% | - | - |
| team_correctness | 20% | - | - |
| data_use_correctness | n/a | 75% | n/a |
| abstention_accuracy | 40% | - | - |
| latency p50 ms | 16341 | - | - |
| latency p95 ms | 18332 | - | - |
| LLM calls per case | 1.00 | - | - |
| LLM tokens per case | 1080.8 | - | - |
| mean confidence when category and priority match | 0.70 | - | - |
| mean confidence when category or priority is wrong | 0.61 | - | - |

## Failures

### escalation (3)

- cascade ABS-001: expected Other or Security P4, got Other or Security P4. escalation expected Yes, got No; team expected one of ['Operations Analyst'], got (none); abstain case should escalate with low confidence and a follow-up, without inventing an approval
- cascade ABS-002: expected Other or Security P4, got Other or Security P4. escalation expected Yes, got No; team expected one of ['Operations Analyst'], got (none); abstain case should escalate with low confidence and a follow-up, without inventing an approval
- cascade ABS-005: expected Other or Security P4, got Other or Security P4. escalation expected Yes, got No; team expected one of ['Operations Analyst'], got (none); abstain case should escalate with low confidence and a follow-up, without inventing an approval

### category (1)

- cascade ABS-003: expected Other or Security P4, got Product Quality and Safety P2. category expected Other or Security, got Product Quality and Safety; priority expected P4, got P2; team expected one of ['Operations Analyst'], got Store Manager + Product Quality

### priority (1)

- cascade ROB-029: expected POS and Payments P3, got POS and Payments P1. priority expected P3, got P1; escalation expected No, got Yes
