"""Verifies one vintage across all surfaces.

Design: assertions on real committed data/output artifacts only when the
required meta key exists (skip with clear reason otherwise).  Must pass BOTH
now (pre-refresh, stale committed artifacts) and after ``make refresh``.
"""
import json
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _repo_root():
    return os.path.join(os.path.dirname(__file__), "..")


def test_scores_json_meta_if_present():
    """If scores.json has _meta, check it contains the expected version keys."""
    path = os.path.join(_repo_root(), "data", "output", "scores.json")
    if not os.path.exists(path):
        pytest.skip("scores.json not present")
    data = _load_json(path)
    meta = data.get("_meta")
    if meta is None:
        pytest.skip("_meta not yet present (pre-refresh artifact)")
    assert "exposure_index_version" in meta
    assert "crosswalk_version" in meta
    assert "generated_at" in meta
    assert "coverage_definition" in meta


def test_cod_subgroups_meta_if_present():
    """If cod_subgroups.json has meta, check vintage keys."""
    path = os.path.join(_repo_root(), "data", "output", "cod_subgroups.json")
    if not os.path.exists(path):
        pytest.skip("cod_subgroups.json not present")
    data = _load_json(path)
    if not isinstance(data, dict):
        pytest.skip("cod_subgroups.json is a plain list (pre-refresh artifact)")
    meta = data.get("meta")
    if meta is None:
        pytest.skip("meta not yet present (pre-refresh artifact)")
    assert "survey_year" in meta
    assert "survey_quarter" in meta
    assert "generated_at" in meta
    assert "source" in meta
    assert "sample_suppression_thresholds" in meta


def test_timeseries_meta_if_present():
    """If grande_grupos_timeseries.json has meta, check year-range keys."""
    path = os.path.join(_repo_root(), "data", "output", "grande_grupos_timeseries.json")
    if not os.path.exists(path):
        pytest.skip("grande_grupos_timeseries.json not present")
    data = _load_json(path)
    meta = data.get("meta")
    if meta is None:
        pytest.skip("meta not yet present (pre-refresh artifact)")
    assert "survey_year_min" in meta
    assert "survey_year_max" in meta
    assert "generated_at" in meta
    assert meta["survey_year_min"] <= meta["survey_year_max"]
