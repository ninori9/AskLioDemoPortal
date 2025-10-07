import pytest

class DummyDB:
    """No-op SQLAlchemy-like session for unit tests."""
    def add(self, *args, **kwargs): pass
    def commit(self): pass
    def refresh(self, *args, **kwargs): pass
    def query(self, *args, **kwargs):
        # Return an object that supports .order_by(...).all() and .first()
        class _Q:
            def order_by(self, *a, **k): return self
            def all(self): return []
            def first(self): return [1]  # used as fallback commodity group id
            def filter(self, *a, **k): return self
        return _Q()

@pytest.fixture
def db():
    return DummyDB()

@pytest.fixture
def fake_classifier(monkeypatch):
    """Monkeypatch a deterministic commodity classifier."""
    class DummyClassifier:
        def run(self, _input):
            return type(
                "Res", (), {"suggested_commodity_group_id": 31, "confidence": 0.87}
            )
    class DummyRegistry:
        commodity_classifier = DummyClassifier()
    monkeypatch.setattr(
        "app.services.procurement_service.get_agent_registry",
        lambda: DummyRegistry(),
    )

@pytest.fixture
def mute_weaviate(monkeypatch):
    """Prevent outbound calls to Weaviate/AI during tests."""
    monkeypatch.setattr("app.services.procurement_service.get_ai_client", lambda: None)
    monkeypatch.setattr("app.services.procurement_service.wx", type("WX", (), {
        "add": staticmethod(lambda **kwargs: None),
        "update_commodity_group": staticmethod(lambda **kwargs: 0),
    }))