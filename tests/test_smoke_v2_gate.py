from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from kalshi_mm.smoke_v2_gate import V2AuthorizationError, validate_launch

ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 10, 13, 19, 0, tzinfo=ET).astimezone(UTC)


def approved_candidate() -> dict:
    return {
        "schema_version": "2.0",
        "verification_id": "e001-smoke-verification-v2",
        "authorization": "24h_non_performance_integrity_verification_only",
        "authorized_by": "project_owner",
        "decision_ref": "ChatGPT owner approval 2026-10-13",
        "public_read_only_only": True,
        "official_e001_30_day_authorized": False,
        "performance_view_authorized": False,
        "orders_authorized": False,
        "real_money_authorized": False,
        "paid_capacity_authorized": False,
        "retention_days": 0,
        "storage_backend": "github_release_assets",
        "release_payload_public_api_only": True,
        "actions_artifacts_enabled": False,
        "collector_commit_sha": "a" * 40,
        "earliest_launch_utc": (NOW - timedelta(minutes=5)).isoformat(),
        "latest_launch_utc": (NOW + timedelta(minutes=20)).isoformat(),
    }


def test_prospective_24h_smoke_only_after_recent_capacity_check():
    result = validate_launch(approved_candidate(), now=NOW)
    assert result["storage_gate"] == "release_assets_no_actions_artifacts"
    assert result["public_read_only_only"] == "true"


@pytest.mark.parametrize("field", [
    "authorization", "verification_id", "authorized_by", "public_read_only_only",
    "official_e001_30_day_authorized", "performance_view_authorized",
    "orders_authorized", "real_money_authorized", "paid_capacity_authorized",
    "retention_days", "decision_ref", "storage_backend",
    "release_payload_public_api_only", "actions_artifacts_enabled",
])
def test_missing_gate_fields_fail_closed(field):
    auth = approved_candidate()
    auth.pop(field)
    with pytest.raises(V2AuthorizationError):
        validate_launch(auth, now=NOW)


@pytest.mark.parametrize("field", [
    "orders_authorized", "real_money_authorized", "performance_view_authorized",
    "official_e001_30_day_authorized", "paid_capacity_authorized",
])
def test_prohibited_authorizations_cannot_be_enabled(field):
    auth = approved_candidate()
    auth[field] = True
    with pytest.raises(V2AuthorizationError):
        validate_launch(auth, now=NOW)


def test_old_smoke_marker_fails_closed():
    auth = approved_candidate()
    auth["authorization"] = "24h_non_performance_integrity_smoke_only"
    with pytest.raises(V2AuthorizationError):
        validate_launch(auth, now=NOW)


def test_artifact_or_paid_storage_backend_is_forbidden():
    for wrong in ("actions_artifacts", "packages", "s3", None):
        auth = approved_candidate()
        auth["storage_backend"] = wrong
        with pytest.raises(V2AuthorizationError):
            validate_launch(auth, now=NOW)


def test_private_or_paid_artifact_flags_are_rejected():
    for field, value in (
        ("release_payload_public_api_only", False),
        ("actions_artifacts_enabled", True),
        ("paid_capacity_authorized", True),
    ):
        auth = approved_candidate()
        auth[field] = value
        with pytest.raises(V2AuthorizationError):
            validate_launch(auth, now=NOW)


def test_launch_before_after_window_blocked():
    auth = approved_candidate()
    for other in (NOW - timedelta(hours=1), NOW + timedelta(hours=1)):
        with pytest.raises(V2AuthorizationError, match="launch window"):
            validate_launch(auth, now=other)


def test_launch_at_midday_fails_without_full_next_session():
    lunchtime = datetime(2026, 10, 13, 12, 0, tzinfo=ET).astimezone(UTC)
    auth = approved_candidate()
    auth["earliest_launch_utc"] = (lunchtime - timedelta(minutes=1)).isoformat()
    auth["latest_launch_utc"] = (lunchtime + timedelta(minutes=1)).isoformat()
    with pytest.raises(V2AuthorizationError, match="quote session"):
        validate_launch(auth, now=lunchtime)


def test_window_cannot_span_several_days():
    auth = approved_candidate()
    auth["latest_launch_utc"] = (NOW + timedelta(days=2)).isoformat()
    with pytest.raises(V2AuthorizationError, match="1 hour"):
        validate_launch(auth, now=NOW)


def test_unzoned_launch_time_fails():
    auth = approved_candidate()
    auth["earliest_launch_utc"] = "2026-10-13T19:00:00"
    with pytest.raises(V2AuthorizationError, match="timezone"):
        validate_launch(auth, now=NOW)


def test_bad_collector_sha_fails():
    auth = approved_candidate()
    auth["collector_commit_sha"] = "expired"
    with pytest.raises(V2AuthorizationError, match="collector"):
        validate_launch(auth, now=NOW)
