import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

import fetch_ibge_microdata as fim  # noqa: E402


class FakeResponse:
    """Substitui o objeto retornado por urllib.request.urlopen em testes (sem rede)."""

    def __init__(self, body):
        self._body = body.encode("utf-8")

    def read(self, *_args):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def test_resolve_zip_name_picks_most_recent_revision(monkeypatch):
    html = """
    <a href="PNADC_012020_20220101.zip">PNADC_012020_20220101.zip</a>
    <a href="PNADC_012020_20250815.zip">PNADC_012020_20250815.zip</a>
    <a href="PNADC_022020_20230101.zip">PNADC_022020_20230101.zip</a>
    """
    monkeypatch.setattr(fim.urllib.request, "urlopen", lambda url, timeout=60: FakeResponse(html))

    assert fim.resolve_zip_name("2020", "1", "http://fake/2020/") == "PNADC_012020_20250815.zip"


def test_resolve_zip_name_returns_current_unrevised_name(monkeypatch):
    html = '<a href="PNADC_012026.zip">PNADC_012026.zip</a>'
    monkeypatch.setattr(fim.urllib.request, "urlopen", lambda url, timeout=60: FakeResponse(html))

    assert fim.resolve_zip_name("2026", "1", "http://fake/2026/") == "PNADC_012026.zip"


def test_resolve_zip_name_returns_none_when_quarter_missing(monkeypatch):
    html = '<a href="PNADC_022026.zip">PNADC_022026.zip</a>'
    monkeypatch.setattr(fim.urllib.request, "urlopen", lambda url, timeout=60: FakeResponse(html))

    assert fim.resolve_zip_name("2026", "1", "http://fake/2026/") is None


def test_resolve_zip_name_returns_none_on_http_error(monkeypatch):
    def raise_404(url, timeout=60):
        raise fim.urllib.error.HTTPError(url, 404, "Not Found", None, None)

    monkeypatch.setattr(fim.urllib.request, "urlopen", raise_404)

    assert fim.resolve_zip_name("2099", "1", "http://fake/2099/") is None


def test_fetch_quarter_raises_quarter_unavailable_when_not_published(monkeypatch):
    html = '<a href="PNADC_022026.zip">PNADC_022026.zip</a>'  # só o 2o tri existe
    monkeypatch.setattr(fim.urllib.request, "urlopen", lambda url, timeout=60: FakeResponse(html))

    with pytest.raises(fim.QuarterUnavailable):
        list(fim.fetch_quarter("2026", "1"))


def test_fetch_quarter_propagates_network_failure(monkeypatch):
    html = '<a href="PNADC_012099.zip">PNADC_012099.zip</a>'

    def fake_urlopen(url, timeout=60):
        if url.endswith("/2099/"):
            return FakeResponse(html)
        raise fim.urllib.error.URLError("rede fora do ar")

    monkeypatch.setattr(fim.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(OSError) as exc_info:
        list(fim.fetch_quarter("2099", "1"))
    assert not isinstance(exc_info.value, fim.QuarterUnavailable)
