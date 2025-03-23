import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlmodel import Session, SQLModel

from .app import create_app
from .models import ArticleModel, engine


@pytest.fixture()
def app():
    app = create_app()
    SQLModel.metadata.create_all(engine)
    yield app
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_get_success(client: FlaskClient):
    with Session(engine) as session:
        article = ArticleModel(title="Test title", content="Test content")
        session.add(article)
        session.commit()
        session.refresh(article)

    response = client.get("/articles/1")
    assert response.status_code == 200
    assert response.json == {
        "data": {
            "attributes": {"title": "Test title", "content": "Test content"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "relationships": {},
            "type": "articles",
        },
        "errors": None,
        "links": {"self": f"/articles/{article.id}"},
    }


def test_get_not_found(client: FlaskClient):
    response = client.get("/articles/1")
    assert response.status_code == 404
    assert response.json == {
        "data": None,
        "errors": [
            {
                "code": "not_found",
                "detail": "Article not found",
                "source": None,
                "status": "404",
                "title": "Not found",
            }
        ],
        "links": {},
    }
