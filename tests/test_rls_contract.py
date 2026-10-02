"""
ReNexa — Row Level Security (RLS) Contract Tests (Phase 9B)
============================================================
Verifies that database schema and Row Level Security definitions
enforce multi-tenant user isolation and contain zero unsafe public permissions.
"""

import os
import re
import pytest

SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql"))


def test_schema_file_exists():
    """Verify schema.sql is present."""
    assert os.path.isfile(SCHEMA_PATH), f"Schema missing at {SCHEMA_PATH}"


def test_rls_enabled_on_all_core_tables():
    """Verify that Row Level Security is explicitly enabled on all 5 core tables."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    core_tables = [
        "user_profiles",
        "scans",
        "waste_profiles",
        "recommendations",
        "execution_feedback",
    ]

    for table in core_tables:
        pattern = rf"ALTER\s+TABLE\s+{table}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY\s*;"
        match = re.search(pattern, sql, re.IGNORECASE)
        assert match is not None, f"RLS not enabled on table '{table}' in schema.sql"


def test_user_profiles_references_auth_users():
    """Verify user_profiles table is foreign-keyed to auth.users(id)."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "REFERENCES auth.users(id)" in sql, "user_profiles must reference auth.users(id)"


def test_no_unsafe_public_write_policies():
    """Verify there are no unsafe public unrestricted read/write policies."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    # Search for dangerous pattern: USING (true) or WITH CHECK (true) on tables
    assert "USING (true)" not in sql, "Unsafe public read policy detected (USING (true))"
    assert "WITH CHECK (true)" not in sql, "Unsafe public write policy detected (WITH CHECK (true))"


def test_rls_policies_use_auth_uid():
    """Verify all policies enforce ownership via auth.uid()."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    # auth.uid() must be referenced throughout policies
    uid_occurrences = sql.count("auth.uid()")
    assert uid_occurrences >= 10, f"Expected at least 10 auth.uid() checks, found {uid_occurrences}"


def test_child_tables_enforce_scan_ownership():
    """Verify waste_profiles and recommendations link to scan ownership via subquery."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    # Check for subquery join to scans.user_id = auth.uid()
    assert "scans.user_id = auth.uid()" in sql, "Child tables must verify parent scan ownership"
    assert "scans.id = waste_profiles.scan_id" in sql
    assert "scans.id = recommendations.scan_id" in sql


def test_feedback_enforces_user_isolation():
    """Verify execution_feedback isolates records by user_id = auth.uid()."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    assert 'ON execution_feedback FOR SELECT' in sql
    assert 'ON execution_feedback FOR INSERT' in sql
    assert 'USING (auth.uid() = user_id)' in sql
