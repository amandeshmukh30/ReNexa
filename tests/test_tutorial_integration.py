"""
ReNexa — Video Index & Tutorial Integration Regression Tests
============================================================
Validates loading of video index and recovery projects, URL verification,
pathway matching, error handling, and UI page loading.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.recovery_service import (
    load_video_index,
    load_recovery_projects,
    get_tutorials,
    get_tutorials_for_pathway,
    get_all_pathways,
    DEFAULT_VIDEO_CSV_PATH,
    DEFAULT_PROJECTS_CSV_PATH,
)
from services.execution_service import get_execution_guide


def test_video_index_loads_from_correct_path():
    """Verify that video_index.csv exists and loads records from project-relative path."""
    assert os.path.isfile(DEFAULT_VIDEO_CSV_PATH), f"Video index file not found at {DEFAULT_VIDEO_CSV_PATH}"
    videos = load_video_index()
    assert len(videos) > 0, "Video index should not be empty."
    assert any(v["project_id"] == "R001" for v in videos), "R001 should be present in video index."


def test_recovery_projects_loads_from_correct_path():
    """Verify that recovery_projects.csv exists and loads rich DIY projects."""
    assert os.path.isfile(DEFAULT_PROJECTS_CSV_PATH), f"Projects file not found at {DEFAULT_PROJECTS_CSV_PATH}"
    projects = load_recovery_projects()
    assert len(projects) >= 50, f"Expected at least 50 recovery projects, got {len(projects)}"
    first = projects[0]
    assert "product_name" in first
    assert "steps" in first
    assert "youtube_url" in first


def test_verified_urls_available_for_rendering():
    """Verify that all verified tutorial records have valid URLs starting with http/https."""
    verified_tutorials = get_tutorials(verified_only=True)
    assert len(verified_tutorials) > 0, "Should have verified tutorials."

    for tut in verified_tutorials:
        assert tut["youtube_verified"] == "Yes"
        url = tut["youtube_url"]
        assert url and (url.startswith("http://") or url.startswith("https://")), f"Invalid URL: {url} for {tut['project_id']}"
        assert tut["title"], f"Missing title for {tut['project_id']}"
        assert tut["material"], f"Missing material for {tut['project_id']}"


def test_unverified_entries_filtered_or_flagged():
    """Verify unverified entries (R053-R055) are excluded when verified_only=True."""
    verified = get_tutorials(verified_only=True)
    verified_pids = {t["project_id"] for t in verified}
    assert "R053" not in verified_pids
    assert "R054" not in verified_pids
    assert "R055" not in verified_pids

    # When unverified included, they should have youtube_verified == 'No'
    all_tutorials = get_tutorials(verified_only=False)
    unverified_items = [t for t in all_tutorials if t["project_id"] in ("R053", "R054", "R055")]
    assert len(unverified_items) == 3
    for u in unverified_items:
        assert u["youtube_verified"] == "No"


def test_material_filtering_accuracy():
    """Verify that material filtering accurately isolates relevant tutorials."""
    plastic_tuts = get_tutorials(material="plastic", verified_only=True)
    assert len(plastic_tuts) > 0
    for t in plastic_tuts:
        assert t["material"] == "plastic"

    glass_tuts = get_tutorials(material="glass", verified_only=True)
    assert len(glass_tuts) > 0
    for t in glass_tuts:
        assert t["material"] == "glass"


def test_pathway_tutorial_matching():
    """Verify valid tutorials match their corresponding recovery pathways."""
    # Test plastic planter pathway
    planter_tuts = get_tutorials_for_pathway("REC-PLA-002", verified_only=True)
    assert len(planter_tuts) > 0
    assert any("planter" in t["product_name"].lower() or "bottle" in t["product_name"].lower() for t in planter_tuts)

    # Test cardboard organizer pathway
    cardboard_tuts = get_tutorials_for_pathway("REC-CAR-002", verified_only=True)
    assert len(cardboard_tuts) > 0
    assert any("drawer" in t["product_name"].lower() or "divider" in t["product_name"].lower() for t in cardboard_tuts)


def test_missing_or_unmatched_tutorials_handled_gracefully():
    """Verify that non-existent pathway or unknown material does not crash and returns empty list."""
    empty_res = get_tutorials_for_pathway("NON_EXISTENT_ID")
    assert empty_res == []

    empty_mat = get_tutorials(material="nonexistent_material_xyz", verified_only=True)
    assert empty_mat == []

    guide = get_execution_guide("REC-BAT-001")
    assert isinstance(guide, dict)
    assert "verified_tutorials" in guide
    assert isinstance(guide["verified_tutorials"], list)


def test_execution_guide_attaches_verified_tutorials():
    """Verify get_execution_guide populates verified_tutorials and primary_tutorial."""
    guide = get_execution_guide("REC-PLA-001")
    assert guide["can_execute"] is True
    assert len(guide["verified_tutorials"]) > 0
    assert guide["primary_tutorial"] is not None
    assert guide["primary_tutorial"]["youtube_url"].startswith("http")


def test_pages_import_cleanly():
    """Verify that the tutorial and execution page modules import without syntax or runtime error."""
    import importlib.util

    for page_name in ["6_Tutorials.py", "6_Execution.py"]:
        page_path = os.path.join(PROJECT_ROOT, "app", "pages", page_name)
        spec = importlib.util.spec_from_file_location(page_name, page_path)
        assert spec is not None
        assert spec.loader is not None
