# E001 Collector Rebuild

**REBUILT FROM CANONICAL E001 SPECIFICATION**

The exact prior collector implementation was lost. Recovery of the known repository history and recovery artifacts was exhausted, and the project owner authorized a clean replacement. This implementation is built from the current `main` commit and `research/E001_PREREGISTRATION.md`, which remains the source of truth for E001 parameters and methodology.

The methodology is unchanged: `KXHIGHNY` only, public REST observation, the frozen America/New_York quote window and cadence, immutable raw evidence, conservative queue accounting, and the preregistered limits. Partial recovered files are not represented as the lost full source. No performance, validation, or OOS evidence was viewed, and the 30-day E001 window was not started.

The replacement is read-only and has no order endpoint, credentials, authenticated client, execution adapter, P&L calculation, or economic evaluator. Smoke output is limited to data integrity, market/book validity, hypothetical quote state, queue consumption, hypothetical fills, and inventory/safety transitions.

Bounded chunks may be stopped and restarted. Append-only compressed observations and their manifest preserve raw evidence, while restart state preserves cadence due-times and trade cursor/watermark lineage. Missing scheduled observations remain explicit gaps and are never synthesized or backfilled.
