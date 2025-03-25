import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from .app import create_app
from .models import ArticleModel, Base, engine


@pytest.fixture()
def app():
    app = create_app()
    Base.metadata.create_all(engine)
    yield app
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


@pytest.fixture()
def article(app) -> ArticleModel:
    with Session(engine) as session:
        article = ArticleModel(title="Test title", content="Test content")
        session.add(article)
        session.commit()
        session.refresh(article)
    return article


def test_get_success(article: ArticleModel, client: FlaskClient):
    response = client.get(f"/articles/{article.id}")
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


def test_edit(article: ArticleModel, client: FlaskClient):
    response = client.patch(
        f"/articles/{article.id}",
        json={
            "data": {
                "type": "articles",
                "id": str(article.id),
                "attributes": {"content": "New content", "title": "New title"},
            }
        },
    )
    assert response.status_code == 200
    assert response.json == {
        "data": {
            "attributes": {"content": "New content", "title": "New title"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "relationships": {},
            "type": "articles",
        },
        "errors": None,
        "links": {"self": f"/articles/{article.id}"},
    }


def test_edit_one_field(article: ArticleModel, client: FlaskClient):
    response = client.patch(
        f"/articles/{article.id}",
        json={
            "data": {
                "type": "articles",
                "id": str(article.id),
                "attributes": {"title": "New title"},
            }
        },
    )
    assert response.status_code == 200
    assert response.json == {
        "data": {
            "attributes": {"title": "New title", "content": "Test content"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "relationships": {},
            "type": "articles",
        },
        "errors": None,
        "links": {"self": f"/articles/{article.id}"},
    }


def test_edit_no_fields(article: ArticleModel, client: FlaskClient):
    response = client.patch(
        f"/articles/{article.id}",
        json={"data": {"type": "articles", "id": str(article.id), "attributes": {}}},
    )
    assert response.status_code == 400
    assert response.json == {
        "data": None,
        "errors": [
            {
                "code": "bad_request",
                "detail": "At least one attribute must be set",
                "source": None,
                "status": "400",
                "title": "Bad request",
            }
        ],
        "links": {},
    }


def test_edit_validation_error(article: ArticleModel, client: FlaskClient):
    response = client.patch(
        f"/articles/{article.id}",
        json={
            "data": {
                "type": "articles",
                "id": str(article.id),
                "attributes": {"title": 4},
            }
        },
    )
    assert response.status_code == 400
    assert response.json == {
        "data": None,
        "errors": [
            {
                "code": "bad_request",
                "detail": "Input should be a valid string",
                "source": {"pointer": "/attributes/title"},
                "status": "400",
                "title": "string_type",
            }
        ],
        "links": {},
    }
