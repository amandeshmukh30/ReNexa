"""
ReNexa — Database Persistence Tests (Phase 9A)
==============================================
Verifies database data models, configuration detection, local fallback persistence,
input validation, error resilience, and secret masking without requiring live Supabase credentials.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from database.models import (
    generate_uuid,
    get_utc_timestamp,
    create_scan_record,
    create_waste_profile_record,
    create_recommendation_record,
    create_feedback_record,
)
from database.database import (
    get_supabase_config,
    is_database_configured,
    get_database_status,
    save_scan,
    save_waste_profile,
    save_recommendation,
    save_recommendations,
    save_execution_feedback,
    get_user_scans,
    get_scan_recommendations,
    get_user_feedback,
    get_all_feedback,
    LOCAL_FILES,
    SupabaseClient,
)


def test_uuid_and_timestamp_generation():
    """Verify UUID and UTC timestamp formatting."""
    uid1 = generate_uuid()
    uid2 = generate_uuid()
    assert isinstance(uid1, str)
    assert len(uid1) == 36
    assert uid1 != uid2

    ts = get_utc_timestamp()
    assert isinstance(ts, str)
    assert ts.endswith("Z")


def test_configuration_detection_when_missing():
    """Verify clean fallback when environment variables are empty."""
    with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""}, clear=True):
        cfg = get_supabase_config()
        assert cfg["url"] is None
        assert cfg["anon_key"] is None
        assert is_database_configured() is False


def test_configuration_detection_when_present():
    """Verify recognition when credentials are set in environment."""
    with patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://xyzcompany.supabase.co", "SUPABASE_ANON_KEY": "dummy-anon-key-123"},
    ):
        cfg = get_supabase_config()
        assert cfg["url"] == "https://xyzcompany.supabase.co"
        assert cfg["anon_key"] == "dummy-anon-key-123"
        assert is_database_configured() is True


def test_database_status_never_leaks_secrets():
    """Verify get_database_status masks URL and never contains raw secret keys."""
    raw_key = "super-secret-jwt-key-99999"
    with patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://myproj123456.supabase.co", "SUPABASE_ANON_KEY": raw_key},
    ):
        status = get_database_status()
        assert status["configured"] is True
        assert status["mode"] == "supabase_postgresql"
        assert raw_key not in json.dumps(status)
        assert "..." in status["url_masked"]


def test_scan_record_validation():
    """Verify structure and normalization of scan record creation."""
    rec = create_scan_record(
        detected_material="PLASTIC",
        model_label="plastic_bottle",
        confidence=0.925,
        detected_object_count=2,
        confirmed_quantity=3,
        image_filename="test_bottle.jpg",
    )
    assert rec["detected_material"] == "plastic"
    assert rec["model_label"] == "plastic_bottle"
    assert rec["confidence"] == 0.925
    assert rec["detected_object_count"] == 2
    assert rec["confirmed_quantity"] == 3
    assert rec["image_filename"] == "test_bottle.jpg"
    assert len(rec["id"]) == 36
    assert rec["created_at"].endswith("Z")


def test_waste_profile_record_validation():
    """Verify waste profile model construction linked to scan."""
    scan_id = generate_uuid()
    prof = create_waste_profile_record(
        scan_id=scan_id,
        material="glass",
        condition="clean",
        contamination="none",
        confirmed_quantity=2,
        item="Glass Bottle",
        material_breakdown={"glass": 2},
    )
    assert prof["scan_id"] == scan_id
    assert prof["material"] == "glass"
    assert prof["condition"] == "clean"
    assert prof["contamination"] == "none"
    assert prof["confirmed_quantity"] == 2
    assert prof["item"] == "Glass Bottle"
    assert prof["material_breakdown"] == {"glass": 2}


def test_recommendation_record_validation():
    """Verify recommendation model construction."""
    scan_id = generate_uuid()
    rec = create_recommendation_record(
        scan_id=scan_id,
        pathway_id="rec-pla-001",
        pathway_title="Plastic Container Storage",
        pathway_type="REUSE",
        rank=1,
        mcda_score=94.5,
        criterion_scores={"practical_fit": 100.0, "recovery_value": 85.0},
        why_this=["Budget fits user ₹0 limit"],
    )
    assert rec["scan_id"] == scan_id
    assert rec["pathway_id"] == "REC-PLA-001"
    assert rec["pathway_type"] == "reuse"
    assert rec["rank"] == 1
    assert rec["mcda_score"] == 94.5
    assert rec["criterion_scores"]["practical_fit"] == 100.0
    assert len(rec["why_this"]) == 1


def test_feedback_record_validation():
    """Verify feedback record model construction."""
    fb = create_feedback_record(
        pathway_id="rec-met-001",
        pathway_title="Metal Can Pen Stand",
        attempt_status="successful",
        material="metal",
        estimated_time_minutes=10,
        actual_time_minutes=8,
        user_rating=5,
    )
    assert fb["pathway_id"] == "REC-MET-001"
    assert fb["attempt_status"] == "successful"
    assert fb["material"] == "metal"
    assert fb["estimated_time_minutes"] == 10
    assert fb["actual_time_minutes"] == 8
    assert fb["user_rating"] == 5
    assert fb["missing_tools"] is False


def test_local_fallback_persistence_roundtrip():
    """Verify saving and retrieving records via local file fallback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_scans_file = os.path.join(tmpdir, "scans.json")
        test_recs_file = os.path.join(tmpdir, "recommendations.json")
        test_fb_file = os.path.join(tmpdir, "outcome_feedback.json")

        with patch.dict(
            LOCAL_FILES,
            {
                "scans": test_scans_file,
                "recommendations": test_recs_file,
                "execution_feedback": test_fb_file,
            },
        ), patch("database.database.is_database_configured", return_value=False):
            # 1. Save scan
            s = save_scan({
                "detected_material": "plastic",
                "confidence": 0.88,
                "confirmed_quantity": 2,
            })
            assert os.path.isfile(test_scans_file)
            scans_list = get_user_scans()
            assert len(scans_list) == 1
            assert scans_list[0]["detected_material"] == "plastic"

            # 2. Save recommendations
            save_recommendations(
                [
                    {"pathway_id": "REC-PLA-001", "rank": 1, "score": 90.0, "title": "Option 1"},
                    {"pathway_id": "REC-PLA-002", "rank": 2, "score": 85.0, "title": "Option 2"},
                ],
                scan_id=s["id"],
            )
            assert os.path.isfile(test_recs_file)
            matched_recs = get_scan_recommendations(s["id"])
            assert len(matched_recs) == 2
            assert matched_recs[0]["rank"] == 1

            # 3. Save feedback
            fb = save_execution_feedback({
                "pathway_id": "REC-PLA-001",
                "attempt_status": "successful",
                "scan_id": s["id"],
            })
            assert os.path.isfile(test_fb_file)
            all_fb = get_all_feedback()
            assert len(all_fb) == 1
            assert all_fb[0]["pathway_id"] == "REC-PLA-001"


def test_malformed_input_handling_never_crashes():
    """Verify robust handling of empty, None, or invalid inputs."""
    with patch("database.database.is_database_configured", return_value=False):
        res_scan = save_scan(None)  # type: ignore
        assert res_scan is not None
        assert "id" in res_scan

        res_prof = save_waste_profile(None)  # type: ignore
        assert res_prof is not None
        assert "id" in res_prof

        res_rec = save_recommendation(None)  # type: ignore
        assert res_rec is not None

        res_recs = save_recommendations(None)  # type: ignore
        assert res_recs == []

        res_fb = save_execution_feedback(None)  # type: ignore
        assert res_fb is not None


def test_supabase_client_mock_insert():
    """Verify SupabaseClient REST dispatch with mocked requests."""
    client = SupabaseClient(url="https://fake.supabase.co", anon_key="fake-anon-key")
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = [{"id": "uuid-123", "detected_material": "glass"}]
        mock_post.return_value = mock_resp

        result = client.insert("scans", {"detected_material": "glass"})
        assert result["id"] == "uuid-123"
        assert result["detected_material"] == "glass"
        mock_post.assert_called_once()
        assert mock_post.call_args[1]["headers"]["apikey"] == "fake-anon-key"


def test_supabase_client_network_error_handled_safely():
    """Verify network exceptions in SupabaseClient return None without raising unhandled error."""
    client = SupabaseClient(url="https://fake.supabase.co", anon_key="fake-anon-key")
    with patch("requests.post", side_effect=Exception("Connection refused")):
        res = client.insert("scans", {"detected_material": "metal"})
        assert res is None


@pytest.mark.skipif(
    not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_ANON_KEY"),
    reason="Optional live Supabase credentials not configured in environment",
)
def test_live_supabase_integration_optional():
    """Optional live integration test executed ONLY when real credentials are present."""
    client = SupabaseClient(
        url=os.environ["SUPABASE_URL"],
        anon_key=os.environ["SUPABASE_ANON_KEY"],
    )
    # Simple query to verify endpoint connectivity
    records = client.query("scans", params={"limit": "1"})
    assert records is not None
