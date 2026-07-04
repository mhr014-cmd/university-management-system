"""
Unit tests: app.main.create_app — Milestone 11 docs-gating hardening.

Verifies /docs, /redoc, /openapi.json are enabled in every environment
except "production" (System_Architecture.md §11), without needing a live
server — inspects the constructed FastAPI app's own docs_url/redoc_url/
openapi_url attributes directly.
"""

from app.main import create_app, settings


def test_docs_enabled_by_default_development():
    assert settings.environment == "development"
    app = create_app()
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


def test_docs_disabled_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    app = create_app()
    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None


def test_docs_enabled_again_after_leaving_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    prod_app = create_app()
    assert prod_app.docs_url is None

    monkeypatch.setattr(settings, "environment", "development")
    dev_app = create_app()
    assert dev_app.docs_url == "/docs"
