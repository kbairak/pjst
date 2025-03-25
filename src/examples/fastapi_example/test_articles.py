import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from .app import app
from .models import ArticleModel, Base, engine

client = TestClient(app)


@pytest.fixture()
def db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def test_article_found(db):
    with Session(engine) as session:
        article = ArticleModel(title="Test title", content="Test content")
        session.add(article)
        session.commit()
        session.refresh(article)
    response = client.get("/articles/1")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "attributes": {"content": "Test content", "title": "Test title"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "relationships": {},
            "type": "articles",
        },
        "errors": None,
        "links": {"self": f"/articles/{article.id}"},
    }


def test_article_not_found(db):
    response = client.get("/articles/1")
    assert response.status_code == 404
