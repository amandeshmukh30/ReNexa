"""
ReNexa — Production Hardening & Deployment Readiness Tests (Phase 9D)
====================================================================
Verifies repository-relative path resolution, Streamlit Cloud configuration,
required runtime assets, secret masking, and fault-tolerant error handling.
"""

import os
import re
import pytest
from unittest.mock import patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_required_runtime_data_files_exist():
    """Verify that all core runtime CSV and JSON template data files exist."""
    required_files = [
        os.path.join(PROJECT_ROOT, "data", "recovery_pathways.csv"),
        os.path.join(PROJECT_ROOT, "data", "safety_rules.csv"),
        os.path.join(PROJECT_ROOT, "data", "outcome_feedback.json"),
    ]
    for path in required_files:
        assert os.path.isfile(path), f"Critical runtime asset missing: {path}"


def test_model_file_exists_and_path_is_repository_relative():
    """Verify AI model weights exist at repository-relative path."""
    from ai.model_config import MODEL_PATH, REPO_MODEL_PATH
    assert os.path.isfile(MODEL_PATH), f"Model file not found at {MODEL_PATH}"
    assert os.path.isfile(REPO_MODEL_PATH), f"Repository model missing at {REPO_MODEL_PATH}"
    # Verify no developer username hardcoding
    assert "C:\\Users\\" not in REPO_MODEL_PATH


def test_requirements_file_validity():
    """Verify requirements.txt exists and specifies essential packages."""
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    assert os.path.isfile(req_path), "requirements.txt missing from repository root"

    with open(req_path, "r", encoding="utf-8") as f:
        content = f.read().lower()

    essential_packages = [
        "streamlit",
        "ultralytics",
        "torch",
        "pillow",
        "pandas",
        "numpy",
        "requests",
    ]
    for pkg in essential_packages:
        assert pkg in content, f"Essential package '{pkg}' missing from requirements.txt"


def test_authoritative_streamlit_config():
    """Verify single root .streamlit/config.toml exists and duplicate app/.streamlit is absent."""
    root_config = os.path.join(PROJECT_ROOT, ".streamlit", "config.toml")
    duplicate_config = os.path.join(PROJECT_ROOT, "app", ".streamlit", "config.toml")

    assert os.path.isfile(root_config), "Root .streamlit/config.toml is missing"
    assert not os.path.exists(duplicate_config), "Duplicate app/.streamlit config must be removed"


def test_gitignore_protects_secrets_and_caches():
    """Verify .gitignore includes .env, secrets.toml, venv, and test cache patterns."""
    gitignore_path = os.path.join(PROJECT_ROOT, ".gitignore")
    assert os.path.isfile(gitignore_path)

    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    patterns = [".env", "secrets.toml", "venv", "__pycache__", ".pytest_cache"]
    for p in patterns:
        assert p in content, f"Pattern '{p}' missing from .gitignore"


def test_no_hardcoded_developer_paths_in_production_code():
    """Scan all Python production files for hardcoded Windows user paths."""
    scan_dirs = ["ai", "app", "database", "services", "utils"]
    pattern = re.compile(r'C:\\Users\\[a-zA-Z0-9_-]+', re.IGNORECASE)

    violations = []
    for sdir in scan_dirs:
        full_dir = os.path.join(PROJECT_ROOT, sdir)
        for root, _, files in os.walk(full_dir):
            for file in files:
                if file.endswith(".py"):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if pattern.search(line):
                                violations.append(f"{fpath}:{idx} -> {line.strip()}")

    assert not violations, f"Hardcoded developer paths found in production code:\n" + "\n".join(violations)


def test_streamlit_secrets_fallback_support():
    """Verify get_supabase_config loads from st.secrets when available."""
    from database.database import get_supabase_config

    mock_secrets = {
        "SUPABASE_URL": "https://streamlit-cloud.supabase.co",
        "SUPABASE_ANON_KEY": "streamlit-anon-secret-key-999",
    }

    with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_ANON_KEY": ""}, clear=True):
        with patch("streamlit.secrets", mock_secrets, create=True):
            cfg = get_supabase_config()
            assert cfg["url"] == "https://streamlit-cloud.supabase.co"
            assert cfg["anon_key"] == "streamlit-anon-secret-key-999"


def test_database_gracefully_handles_invalid_url():
    """Verify SupabaseClient handles malformed or unreachable URL without crashing."""
    from database.database import SupabaseClient
    client = SupabaseClient(url="https://invalid-unreachable-domain-123456789.co", anon_key="key")
    res = client.query("scans")
    assert res is None
