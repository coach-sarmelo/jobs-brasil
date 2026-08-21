"""Tests for the committed site artifact (site/data.json).

The site is static and frozen on the 2026Q1 vintage: site/data.json was
compiled once from data/output/ and is committed as-is. These tests keep the
deployed artifact honest by checking it against the paper's published numbers
(within rounding tolerance) and against the dataset's own meta.
"""
import json
import os

import pytest

REPO = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(REPO, "data", "output")


@pytest.fixture(scope="module")
def site_data():
    path = os.path.join(REPO, "site", "data.json")
    if not os.path.exists(path):
        pytest.skip("site/data.json not present")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_headline_numbers_match_paper(site_data):
    m = site_data["meta"]
    assert m["n"] == 227_629
    assert m["n_occupations"] == 122
    assert m["mean_exposure"] == pytest.approx(2.86, abs=0.05)
    assert m["share_low_exposure"] == pytest.approx(35.2, abs=0.5)
    assert m["low_exposure_jobs_m"] == pytest.approx(35.7, abs=0.2)
    assert m["mean_schooling"] == pytest.approx(11.6, abs=0.2)
    assert m["informality"] == pytest.approx(40.5, abs=1.0)
    assert m["coverage"] == pytest.approx(99.7, abs=0.3)
    assert m["s1_beta"] == pytest.approx(0.23, abs=0.01)
    assert m["s3a_beta"] == pytest.approx(6.2, abs=0.1)


def test_vintage_matches_dataset(site_data):
    artifact = os.path.join(DATA_DIR, "cod_subgroups.json")
    if not os.path.exists(artifact):
        pytest.skip("data/output artifacts not present")
    with open(artifact, encoding="utf-8") as f:
        meta = json.load(f)["meta"]
    v = site_data["meta"]["vintage"]
    assert v["survey_year"] == int(meta["survey_year"])
    assert v["survey_quarter"] == int(meta["survey_quarter"])
    assert v["label"] == f"{meta['survey_quarter']}º tri/{meta['survey_year']}"


def test_occupations_shape(site_data):
    occ = site_data["occupations"]
    assert len(occ) == 124
    assert len([o for o in occ if o["exposure"] is not None]) == 122
    for o in occ:
        assert isinstance(o["code"], str)
        assert o["jobs"] > 0
        if o["exposure"] is not None:
            assert 0 <= o["exposure"] <= 10
        assert 0 <= o["informality"] <= 100


def test_regions_and_ufs(site_data):
    regions = site_data["regions"]
    assert len(regions) == 5
    assert {r["region"] for r in regions} == {"Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"}
    for r in regions:
        assert r["slope"] == pytest.approx(0.07 + 0.28 * r["formality"] / 100, abs=0.002)
    assert [r["slope"] for r in regions] == sorted((r["slope"] for r in regions), reverse=True)
    assert len(site_data["ufs"]) == 27


def test_specs_and_robustness(site_data):
    s = site_data["specs"]
    assert s["S1"]["beta"] == pytest.approx(0.2288, abs=0.001)
    assert s["S3a"]["beta"] == pytest.approx(-6.2285, abs=0.001)
    assert s["S3"]["exposure"]["beta"] == pytest.approx(-3.9068, abs=0.001)
    assert s["S3"]["attenuation"] == pytest.approx(37.2, abs=0.3)
    assert s["S4"]["interaction"]["beta"] == pytest.approx(0.2786, abs=0.001)

    rows = site_data["robustness"]
    assert len(rows) == 13
    assert rows[0]["label"] == "Baseline WLS (S1)"
    assert all(r["label"].startswith("Sem grande grupo") for r in rows[4:])