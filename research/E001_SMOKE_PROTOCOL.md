# E001 Infrastructure Smoke Protocol

This protocol is manual-only. It is not scheduled, has not been run by this rebuild, and does not start E001.

1. Run a bounded collector chunk for the requested wall-clock interval using public REST only.
2. Verify raw segment hashes, per-observation hashes, UTC normalization, monotonic source timestamps, restart state, cursor/watermark continuity, and explicit missed-slot gaps.
3. Replay the immutable segments and compare deterministic counts and payload hashes.
4. Inspect only book/tick validity, microprice inputs, eligibility, hypothetical quote lifecycle, queue consumption, partial hypothetical fills, inventory/safety transitions, and metadata availability.
5. Stop and label data invalid on unresolved cursor gaps, corrupted segments, missing required metadata, or cadence integrity failure.

Smoke output must not contain gross or net P&L, strategy return, Sharpe, drawdown, P&L per fill/contract, economic rankings, or an E001 economic PASS/FAIL. The 30-day performance evaluator is deliberately absent.
