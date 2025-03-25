import json

import django.test
import pytest

from .models import ArticleModel


@pytest.fixture()
def article() -> ArticleModel:
    return ArticleModel.objects.create(title="Test title", content="Test content")


@pytest.mark.django_db
def test_get_article(article: ArticleModel, client: django.test.Client):
    response = client.get(f"/articles/{article.id}")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "type": "articles",
            "id": "1",
            "attributes": {"title": "Test title", "content": "Test content"},
            "relationships": {},
            "links": {"self": f"/articles/{article.id}"},
        },
        "errors": None,
        "links": {"self": f"/articles/{article.id}"},
    }
    assert response.headers["Content-Type"] == "application/vnd.api+json"


@pytest.mark.django_db
def test_get_not_found(client: django.test.Client):
    response = client.get("/articles/1")
    assert response.status_code == 404
    assert response.json() == {
        "data": None,
        "errors": [
            {
                "status": "404",
                "code": "not_found",
                "title": "Not found",
                "detail": "Article not found",
                "source": None,
            }
        ],
        "links": {},
    }
    assert response.headers["Content-Type"] == "application/vnd.api+json"


@pytest.mark.django_db
def test_edit(article: ArticleModel, client: django.test.Client):
    response = client.patch(
        f"/articles/{article.id}",
        data=json.dumps(
            {
                "data": {
                    "type": "articles",
                    "id": str(article.id),
                    "attributes": {"title": "New title", "content": "New content"},
                }
            }
        ),
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "data": {
            "attributes": {"title": "New title", "content": "New content"},
            "id": "1",
            "links": {"self": "/articles/1"},
            "relationships": {},
            "type": "articles",
        },
        "errors": None,
        "links": {"self": "/articles/1"},
    }

    article.refresh_from_db()
    assert (article.title, article.content) == ("New title", "New content")


@pytest.mark.django_db
def test_edit_one_field(article: ArticleModel, client: django.test.Client):
    response = client.patch(
        f"/articles/{article.id}",
        data=json.dumps(
            {
                "data": {
                    "type": "articles",
                    "id": str(article.id),
                    "attributes": {"title": "New title"},
                }
            }
        ),
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "data": {
            "attributes": {"title": "New title", "content": "Test content"},
            "id": "1",
            "links": {"self": "/articles/1"},
            "relationships": {},
            "type": "articles",
        },
        "errors": None,
        "links": {"self": "/articles/1"},
    }

    article.refresh_from_db()
    assert (article.title, article.content) == ("New title", "Test content")


@pytest.mark.django_db
def test_edit_no_fields(article: ArticleModel, client: django.test.Client):
    response = client.patch(
        f"/articles/{article.id}",
        data=json.dumps(
            {"data": {"type": "articles", "id": str(article.id), "attributes": {}}}
        ),
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 400
    assert response.json() == {
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


@pytest.mark.django_db
def test_edit_validation_error(article: ArticleModel, client: django.test.Client):
    response = client.patch(
        f"/articles/{article.id}",
        data=json.dumps(
            {
                "data": {
                    "type": "articles",
                    "id": str(article.id),
                    "attributes": {"title": 4},
                }
            }
        ),
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 400
    assert response.json() == {
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
