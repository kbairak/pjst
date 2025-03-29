import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .app import app

client = TestClient(app)


@pytest.fixture()
def db():
    models.Base.metadata.create_all(models.engine)
    yield
    models.Base.metadata.drop_all(models.engine)


@pytest.fixture()
def article(db) -> models.ArticleModel:
    with Session(models.engine) as session:
        article = models.ArticleModel(title="Test title", content="Test content")
        session.add(article)
        session.commit()
        session.refresh(article)
    return article


def test_article_found(article: models.ArticleModel):
    response = client.get("/articles/1")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "attributes": {"content": "Test content", "title": "Test title"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "type": "articles",
        },
        "links": {"self": f"/articles/{article.id}"},
    }


def test_article_not_found(db):
    response = client.get("/articles/1")
    assert response.status_code == 404


def test_edit(article: models.ArticleModel):
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
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "data": {
            "attributes": {"content": "New content", "title": "New title"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "type": "articles",
        },
        "links": {"self": f"/articles/{article.id}"},
    }


def test_edit_not_found(db):
    response = client.patch(
        "/articles/1",
        json={
            "data": {
                "type": "articles",
                "id": "1",
                "attributes": {"content": "New content", "title": "New title"},
            }
        },
    )
    assert response.status_code == 404
    assert response.json() == {
        "errors": [
            {
                "code": "not_found",
                "detail": "Article with id '1' not found",
                "status": "404",
                "title": "Not found",
            }
        ]
    }


def test_edit_different_id(db):
    response = client.patch(
        "/articles/1",
        json={
            "data": {
                "type": "articles",
                "id": "2",
                "attributes": {"content": "New content", "title": "New title"},
            }
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": [
            {
                "code": "bad_request",
                "detail": "ID in URL (1) does not match ID in body (2)",
                "status": "400",
                "title": "Bad request",
            }
        ]
    }


def test_edit_one_field(article: models.ArticleModel):
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
    assert response.json() == {
        "data": {
            "attributes": {"title": "New title", "content": "Test content"},
            "id": str(article.id),
            "links": {"self": f"/articles/{article.id}"},
            "type": "articles",
        },
        "links": {"self": f"/articles/{article.id}"},
    }


def test_edit_no_fields(article: models.ArticleModel):
    response = client.patch(
        f"/articles/{article.id}",
        json={"data": {"type": "articles", "id": str(article.id), "attributes": {}}},
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": [
            {
                "code": "bad_request",
                "detail": "At least one attribute must be set",
                "source": {"pointer": "/data/attributes"},
                "status": "400",
                "title": "Bad request",
            }
        ],
    }


def test_edit_validation_error(article: models.ArticleModel):
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
    assert response.json() == {
        "errors": [
            {
                "code": "bad_request",
                "detail": "Input should be a valid string",
                "source": {"pointer": "/attributes/title"},
                "status": "400",
                "title": "string_type",
            }
        ],
    }


def test_edit_extra_fields(article: models.ArticleModel):
    response = client.patch(
        f"/articles/{article.id}",
        json={
            "data": {
                "type": "articles",
                "id": str(article.id),
                "attributes": {
                    "title": "New title",
                    "content": "New content",
                    "age": 3,
                },
            }
        },
    )
    assert response.status_code == 400, response.json()
    assert response.json() == {
        "errors": [
            {
                "code": "bad_request",
                "detail": "Extra inputs are not permitted",
                "source": {"pointer": "/attributes/age"},
                "status": "400",
                "title": "extra_forbidden",
            }
        ],
    }


def test_delete_article(article: models.ArticleModel):
    response = client.delete(f"/articles/{article.id}")
    assert response.status_code == 204
    assert response.content == b""
    with Session(models.engine) as session:
        assert (
            session.scalars(
                select(models.ArticleModel).where(models.ArticleModel.id == article.id)
            ).first()
            is None
        )


def test_delete_article_not_found(db):
    response = client.delete("/articles/1")
    assert response.status_code == 404
    assert response.json() == {
        "errors": [
            {
                "code": "not_found",
                "detail": "Article with id '1' not found",
                "status": "404",
                "title": "Not found",
            }
        ]
    }


def test_get_many(article: models.ArticleModel):
    response = client.get("/articles")
    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "type": "articles",
                "id": str(article.id),
                "attributes": {"content": "Test content", "title": "Test title"},
                "links": {"self": f"/articles/{article.id}"},
            }
        ],
        "links": {"self": "/articles"},
    }
