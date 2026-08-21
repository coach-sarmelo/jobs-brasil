import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

import fetch_historical_microdata as fhm  # noqa: E402

FIXTURE_HISTORICAL = [
    {"grande_grupo": "DIRETORES E GERENTES", "ano": 2015, "total_workers": 100, "avg_income": 5000.0,
     "informality_rate": 10.0, "gender_gap_pct": 20.0, "race_gap_pct": 15.0, "sample_size": 50},
    {"grande_grupo": "OCUPAÇÕES ELEMENTARES", "ano": 2015, "total_workers": 900, "avg_income": 1200.0,
     "informality_rate": 60.0, "gender_gap_pct": None, "race_gap_pct": 5.0, "sample_size": 400},
    {"grande_grupo": "DIRETORES E GERENTES", "ano": 2016, "total_workers": 110, "avg_income": 5200.0,
     "informality_rate": 9.0, "gender_gap_pct": 18.0, "race_gap_pct": 14.0, "sample_size": 55},
    {"grande_grupo": "OCUPAÇÕES ELEMENTARES", "ano": 2016, "total_workers": 890, "avg_income": 1250.0,
     "informality_rate": 58.0, "gender_gap_pct": None, "race_gap_pct": 4.5, "sample_size": 410},
    {"grande_grupo": "DIRETORES E GERENTES", "ano": 2017, "total_workers": 120, "avg_income": 5400.0,
     "informality_rate": 8.5, "gender_gap_pct": 17.0, "race_gap_pct": 13.0, "sample_size": 60},
    {"grande_grupo": "OCUPAÇÕES ELEMENTARES", "ano": 2017, "total_workers": 880, "avg_income": 1300.0,
     "informality_rate": 57.0, "gender_gap_pct": None, "race_gap_pct": 4.0, "sample_size": 420},
]


def test_build_timeseries_consolidates_by_grande_grupo():
    timeseries = fhm.build_timeseries(FIXTURE_HISTORICAL)

    assert set(timeseries.keys()) == {"DIRETORES E GERENTES", "OCUPAÇÕES ELEMENTARES"}

    diretores = timeseries["DIRETORES E GERENTES"]
    assert [p["ano"] for p in diretores] == [2015, 2016, 2017]
    assert "grande_grupo" not in diretores[0]
    assert diretores[0]["total_workers"] == 100
    assert diretores[-1]["avg_income"] == 5400.0

    elementares = timeseries["OCUPAÇÕES ELEMENTARES"]
    assert elementares[0]["gender_gap_pct"] is None


def test_fetch_historical_stops_on_quarter_unavailable(tmp_path, monkeypatch):
    calls = []

    def fake_process_year(year, *args, **kwargs):
        calls.append(year)
        if year == 2015:
            return [{"grande_grupo": "DIRETORES E GERENTES", "ano": 2015, "total_workers": 100}]
        raise fhm.QuarterUnavailable(f"{year} ainda não publicado")

    monkeypatch.setattr(fhm, "process_year", fake_process_year)
    monkeypatch.setattr(fhm, "OUTPUT_TIMESERIES", str(tmp_path / "out.json"))

    fhm.fetch_historical(2015, 2018)

    # Para no primeiro ano indisponível (2016) e nunca tenta 2017/2018.
    assert calls == [2015, 2016]
    
    with open(str(tmp_path / "out.json")) as f:
        timeseries = json.load(f)
    assert "DIRETORES E GERENTES" in timeseries
    assert timeseries["DIRETORES E GERENTES"][0]["ano"] == 2015


def test_fetch_historical_propagates_unexpected_errors(tmp_path, monkeypatch):
    # Uma falha de rede genuína (não "trimestre ainda não existe") não pode
    # ser tratada como fim silencioso da série histórica — precisa estourar.
    def fake_process_year(year, *args, **kwargs):
        raise OSError("falha de rede inesperada")

    monkeypatch.setattr(fhm, "process_year", fake_process_year)

    with pytest.raises(OSError):
        fhm.fetch_historical(2015, 2015)
