"""Fail-closed local launch gate for a separately authorized 24h E001 smoke.

No network access. Never authorizes historical E001 data, economics, or orders.
The original E001 smoke marker is intentionally not accepted.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
AUTHORIZATION = "24h_non_performance_integrity_verification_only"
# Based on original raw artifacts >428 MB with only ~10.6k book batches.
# Future full-coverage collection can exceed 1 GiB, so require substantial
# additional verified free storage for immutable segments and restart state.
MIN_FREE_BYTES = 1_610_612_736  # 1.5 GiB
STORAGE_CONFIRMATION_MAX_AGE = timedelta(hours=24)


class V2AuthorizationError(ValueError):
    """A new E001 smoke may not safely launch."""


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise V2AuthorizationError(f"{field}: timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise V2AuthorizationError(f"{field}: invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise V2AuthorizationError(f"{field}: timezone-aware timestamp required")
    return parsed.astimezone(UTC)


def validate_launch(authorization: dict[str, object], *, now: datetime) -> dict[str, str]:
    if now.tzinfo is None or now.utcoffset() is None:
        raise V2AuthorizationError("current time must be timezone-aware")
    now = now.astimezone(UTC)
    required = {
        "schema_version": "2.0",
        "verification_id": "e001-smoke-verification-v2",
        "authorization": AUTHORIZATION,
        "authorized_by": "project_owner",
        "public_read_only_only": True,
        "official_e001_30_day_authorized": False,
        "performance_view_authorized": False,
        "orders_authorized": False,
        "real_money_authorized": False,
        "paid_capacity_authorized": False,
        "retention_days": 2,
    }
    for key, expected in required.items():
        if authorization.get(key) != expected:
            raise V2AuthorizationError(f"invalid or missing {key!r}")

    collector_commit = authorization.get("collector_commit_sha")
    if (
        not isinstance(collector_commit, str)
        or len(collector_commit) != 40
        or not all(c in "0123456789abcdef" for c in collector_commit)
    ):
        raise V2AuthorizationError("invalid collector_commit_sha")
    if not isinstance(authorization.get("decision_ref"), str) or not authorization["decision_ref"]:
        raise V2AuthorizationError("explicit owner approval reference required")

    window_start = _timestamp(authorization.get("earliest_launch_utc"), "earliest_launch_utc")
    window_end = _timestamp(authorization.get("latest_launch_utc"), "latest_launch_utc")
    if not window_start < window_end or window_end - window_start > timedelta(hours=1):
        raise V2AuthorizationError("launch window must be positive and at most 1 hour")
    if not window_start <= now <= window_end:
        raise V2AuthorizationError("outside prospective preauthorized launch window")

    # A single 24h interval must fully contain the 09:00-15:30 ET session
    # of the *next* calendar day; fail closed on late/early dispatch.
    local_start = now.astimezone(ET)
    next_date = local_start.date() + timedelta(days=1)
    quote_start = datetime.combine(next_date, datetime.min.time(), ET).replace(
        hour=9
    ).astimezone(UTC)
    quote_end = datetime.combine(next_date, datetime.min.time(), ET).replace(
        hour=15, minute=30
    ).astimezone(UTC)
    if not now < quote_start or now + timedelta(hours=24) < quote_end:
        raise V2AuthorizationError("24h window cannot contain complete next-day quote session")
    if not 16 <= local_start.hour <= 22:
        raise V2AuthorizationError("launch must be after today's quote close")

    confirmed_at = _timestamp(
        authorization.get("storage_confirmed_at_utc"), "storage_confirmed_at_utc"
    )
    if confirmed_at > now or now - confirmed_at > STORAGE_CONFIRMATION_MAX_AGE:
        raise V2AuthorizationError("recent GitHub account storage confirmation required")
    available = authorization.get("confirmed_free_storage_bytes")
    if type(available) is not int or available < MIN_FREE_BYTES:
        raise V2AuthorizationError("insufficient confirmed free artifact storage")
    if authorization.get("storage_confirmation_source") != "github_account_billing":
        raise V2AuthorizationError("storage must be verified from GitHub account billing")
    return {
        "verification_id": "e001-smoke-verification-v2",
        "authorization": AUTHORIZATION,
        "window": "authorized_future_24h",
        "collector_commit_sha": collector_commit,
        "public_read_only_only": "true",
        "storage_gate": "confirmed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate new public-data-only smoke gate")
    parser.add_argument("--authorization", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.authorization.read_text())
    if not isinstance(data, dict):
        raise V2AuthorizationError("authorization JSON object required")
    print(json.dumps(validate_launch(data, now=datetime.now(UTC)), sort_keys=True))


if __name__ == "__main__":
    main()
