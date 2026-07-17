# Tech Intel Evaluation Harness - offline-benchmark

Quality gate: **PASS**

## Checks
- PASS `top3_count`: top3=3
- PASS `all_candidates_completed_full_flow`: ledger_candidates=6, final_rows=6
- PASS `top3_has_source_urls`: A03, A04, A10
- PASS `top3_evidence_reviewable`: A03=high, A04=high, A10=medium
- PASS `review_packet_requires_human_action`: awaiting_human_review
- PASS `no_blocked_bedrock_candidate_survived`: Bedrock-tagged candidates should be dropped by L0 in this company-account variant.
- PASS `decision_layer_created`: A03=adopt_candidate_after_review, A04=adopt_candidate_after_review, A02=adopt_candidate_after_review
- PASS `feedback_stats_honest_about_sample_size`: insufficient_for_ml_training
- PASS `audit_packet_created`: awaiting_human_review

## Top 3
1. `A03` S3 條件式寫入（conditional writes）支援 ETag 比對，多寫入者免自建鎖（GA） - average 5.0
2. `A04` Step Functions 支援 JSONata 與工作流變數，狀態間傳值不再需要 Pass 疊疊樂（GA） - average 4.55
3. `A10` EventBridge Scheduler 新增排程群組配額提升與失敗重試指標（GA） - average 4.2

## Decision Layer
1. `A03` decision_score=5.47 action=adopt_candidate_after_review
2. `A04` decision_score=5.08 action=adopt_candidate_after_review
3. `A02` decision_score=4.62 action=adopt_candidate_after_review

## Artifacts
- `benchmark-report.json` contains the evidence ledger, human review packet, decision layer, feedback stats, and audit packet.
