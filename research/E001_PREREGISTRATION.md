# E001 — Prospective Passive-Quote Viability

Status: **PREREGISTERED — DO NOT EVALUATE YET**  
Preregistered: 2026-09-19  
Performance viewed before freeze: **No**

## Hypothesis

Passive quotes placed under the fixed policy below produce positive expected value after conservative queue-aware fills, partial fills, adverse selection, contemporaneous maker/taker fees, forced-flattening costs, inventory risk, and a fixed capital opportunity cost. Liquidity incentives are reported separately and cannot make E001 pass.

## Research universe

Series: `KXHIGHNY` only (daily highest temperature in NYC).

All active child markets of each daily event are observed. A market is quote-eligible at a decision timestamp only when every eligibility condition below is satisfied. No market/bucket may be excluded later because it loses money.

## Evidence period

- 30 consecutive calendar days.
- The window begins only after the preregistration commit and after a separate 24-hour infrastructure smoke test passes without calculating strategy performance.
- Quote window each eligible calendar day: **09:00:00 through 15:30:00 America/New_York**.
- No E001 P/L or fill-performance metric may be inspected during collection.

## Data cadence and provenance

Target public REST cadence during the quote window:

- full available order-book state: 1 Hz per active KXHIGHNY market (batch endpoint preferred if equivalent)
- public non-block trades: 1 Hz polling with cursor/watermark continuity
- market metadata/rules: at least every 30 seconds and on detected lifecycle change
- exchange status: every 5 seconds
- incentive definitions: every 60 seconds

Raw observations are immutable. Gaps are never filled with later data.

## Market-state eligibility

A hypothetical quote pair can be created only if:

1. market status is `active`;
2. local time is inside the fixed quote window;
3. market `close_time` is at least 60 minutes away;
4. full valid top-of-book exists on both sides;
5. book is not crossed or locked;
6. both displayed top-level sizes are at least **10.00 contracts**;
7. valid tick size is resolved from the market's current `price_ranges`;
8. spread is at least **3 local ticks**;
9. fair value is at least **1 local tick** above the bid and **1 local tick** below the ask;
10. fee metadata and settlement source/rules are resolvable;
11. no exchange/market pause or collector integrity flag is active.

## Fair value

No external forecast model is used.

Let:

- `b` = best YES bid
- `a` = best YES ask implied from the best NO bid
- `Qb` = displayed size at best YES bid
- `Qa` = displayed size at the implied best YES ask (the corresponding best NO bid size)

Then:

- midpoint = `(b + a) / 2`
- **fair value = top-of-book microprice = `(a*Qb + b*Qa) / (Qb + Qa)`**

If any input is unavailable or invalid, do not quote. No fallback forecast is permitted.

## Quote policy

- Quote both sides only; no intentional directional one-sided quoting.
- Hypothetical quote size: **10.00 contracts per side**.
- Bid quote: join current best YES bid.
- Ask quote: join current best YES ask on the unified YES-price scale.
- Never improve through the current best; never cross the spread.
- Only one simulated resting quote per side per market.
- Minimum resting duration: **30 seconds** unless a hard safety cancellation condition occurs.
- Maximum resting duration: **300 seconds**.
- After 30 seconds, cancel/reprice if the best price changes, fair value moves by at least one local tick, spread falls below 3 ticks, or any eligibility condition fails.
- Repricing creates a new queue position from scratch.
- Hard safety cancellation is immediate for market deactivation/close, missing/corrupt book, unresolved tick/fee/rules, or collector integrity failure.
- At **15:30 ET**, cancel all remaining simulated quotes and begin flattening inventory.

## Inventory limits

Inventory is signed YES-equivalent contracts per binary market.

- maximum absolute per-market inventory: **20.00 contracts**
- maximum aggregate absolute inventory across the event: **40.00 contracts**
- a quote that could breach either limit is suppressed on the inventory-increasing side
- opposite-side risk-reducing fills remain allowed

No limit may be raised after results are seen.

## Conservative queue and fill model

For every newly simulated resting quote:

1. `queue_ahead` starts as the **entire displayed resting size already present at our price** at the observation used to create the quote. Our order is assumed last at that price.
2. Cancellations or book-size decreases ahead of us receive **zero credit**. Queue ahead is reduced only by qualifying public trade prints.
3. Block trades are excluded.
4. Public trade direction uses the canonical `taker_book_side` / `taker_outcome_side` fields.
5. A resting YES-bid quote is eligible to fill only from opposing taker-side trade volume printed at that exact YES price; a resting YES-ask quote is treated symmetrically.
6. Same-price qualifying trade volume first consumes `queue_ahead`. Only excess volume can fill our order.
7. Partial fill = `min(remaining_quote_size, max(0, cumulative_qualifying_volume - queue_ahead))`.
8. A mere price touch, later midpoint movement, or unexplained depth disappearance is never counted as a fill.

This deliberately understates fills rather than inventing favorable queue progress.

## Adverse selection

For each simulated fill, compute signed movement of the preregistered microprice against the filled position at:

- 1 second
- 5 seconds
- **30 seconds (primary adverse-selection horizon)**
- 5 minutes

A bid fill is adversely selected when fair value falls; an ask fill is adversely selected when fair value rises. Nominal spread capture and adverse selection are reported separately.

## Flattening and settlement risk

At 15:30 ET, after all resting simulated quotes are canceled:

- flatten remaining inventory immediately against the contemporaneous executable opposite book;
- walk visible depth as necessary and record slippage;
- apply the contemporaneous taker fee to flattening trades;
- never assume hidden liquidity;
- if visible depth is insufficient or the market cannot trade, carry the residual inventory to actual settlement and use the observed settlement payout. This is a realized event-resolution/inventory-risk outcome, not a synthetic exit.

## Fees

Use fee terms observable for the series/event at the time of each simulated execution, including event-level overrides. Apply Kalshi's published rounding rules. Do not lower fees after seeing results.

Current general formulas at preregistration are documented in `research/KALSHI_CURRENT_RESEARCH.md`, but the experiment uses contemporaneous applicable metadata rather than assuming today's multiplier remains unchanged.

## Liquidity incentives

Primary E001 P/L **excludes all incentive/reward income**.

The collector records current public incentive-program definitions. A secondary, explicitly counterfactual analysis may estimate whether our hypothetical resting orders would have been eligible under recorded program parameters, but:

- no simulated reward is called "earned";
- random within-second scoring snapshots and competitor ownership are not assumed observable;
- incentive estimates cannot satisfy promotion criteria;
- if economics are negative without rewards, E001 does not pass.

## Capital opportunity cost

Charge a fixed **5.00% annualized** opportunity cost on committed capital, accrued pro rata by wall-clock time. This rate is deliberately frozen rather than optimized or changed with market conditions.

Committed capital is the maximum collateral locked by simulated resting orders plus open inventory under the exchange's binary-contract economics.

## Metrics

Report at minimum:

- simulated quote count and quoted contract amount
- fill events, filled contracts, fill rate, partial-fill rate
- average quoted spread and average realized two-sided spread capture
- adverse selection at 1s/5s/30s/5m
- gross spread P/L
- maker fees
- flattening slippage and taker fees
- incentive estimate separately
- opportunity cost
- net P/L excluding incentives
- net P/L including counterfactual incentives (secondary only)
- average/peak inventory, holding duration, time exposed
- max drawdown, worst fill, worst market, daily concentration
- return on committed capital, P/L per filled contract, P/L per quoted dollar
- hypothetical midpoint-mark P/L versus conservative executable P/L

## Data-integrity gate

E001 is economically interpretable only if all of the following hold:

- at least **99.5%** of scheduled order-book polling observations are present during quote windows;
- no unresolved trade-pagination gap affects a period in which a simulated quote was resting;
- UTC timestamps are monotonic per source stream after normalization;
- all simulated fills can be traced to raw qualifying trade records;
- every simulated quote can be traced to raw book, market-state, tick, fee, and rules metadata.

An integrity failure produces `STOP / REJECT — DATA INVALID`; economics are not interpreted. A fresh prospective rerun after an infrastructure fix must receive a new preregistration entry and new dates.

## Promotion criteria — PASS only if every condition holds

1. Data-integrity gate passes.
2. At least **20 distinct days** contain one or more eligible quote opportunities.
3. At least **100 simulated fill events** occur during the 30-day window.
4. Total **net P/L excluding incentives**, after maker fees, flattening costs, taker fees, realized residual settlement outcomes, and opportunity cost, is greater than zero.
5. The lower bound of a **95% day-block bootstrap confidence interval** for net P/L per filled contract is greater than zero. Use 10,000 bootstrap resamples of whole calendar days and fixed RNG seed `3001`.
6. No inventory or safety limit breach occurred in the simulation engine.

Passing promotes the project only to designing the next preregistered research experiment. It does not authorize real-money trading.

## Rejection / stopping criteria

Record `STOP / REJECT` if any of the following occurs:

- realistic fills plus adverse selection, fees, flattening, settlement outcomes, and opportunity cost produce non-positive total net P/L excluding incentives;
- the 95% bootstrap lower bound is not above zero;
- fewer than 20 opportunity days or fewer than 100 fill events occur in the fixed 30-day window;
- profitability exists only after adding incentive estimates;
- the data-integrity gate fails (label as data invalid and do not interpret strategy economics).

Do not respond to rejection by assuming better queue position, counting touches as fills, lowering fees, removing losing buckets, increasing inventory, changing quote width, or extending the evidence window. Any materially different policy is a new preregistered experiment.
