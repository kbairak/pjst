import json

import django.test
import pytest

from .models import ArticleModel


@pytest.fixture()
def article() -> ArticleModel:
    return ArticleModel.objects.create(title="Test title", content="Test content")


@pytest.mark.django_db
def test_get_one(article: ArticleModel, client: django.test.Client):
    response = client.get(f"/articles/{article.id}")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "type": "articles",
            "id": "1",
            "attributes": {"title": "Test title", "content": "Test content"},
            "links": {"self": f"/articles/{article.id}"},
        },
        "links": {"self": f"/articles/{article.id}"},
    }
    assert response.headers["Content-Type"] == "application/vnd.api+json"


@pytest.mark.django_db
def test_get_one_not_found(client: django.test.Client):
    response = client.get("/articles/1")
    assert response.status_code == 404
    assert response.json() == {
        "errors": [
            {
                "status": "404",
                "code": "not_found",
                "title": "Not found",
                "detail": "Article not found",
            }
        ],
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
            "type": "articles",
        },
        "links": {"self": "/articles/1"},
    }

    article.refresh_from_db()
    assert (article.title, article.content) == ("New title", "New content")


@pytest.mark.django_db
def test_edit_one_not_found(client: django.test.Client):
    response = client.patch(
        "/articles/1",
        data=json.dumps(
            {
                "data": {
                    "type": "articles",
                    "id": "1",
                    "attributes": {"title": "New title", "content": "New content"},
                }
            }
        ),
        content_type="application/vnd.api+json",
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


@pytest.mark.django_db
def test_edit_one_different_id(client: django.test.Client):
    response = client.patch(
        "/articles/1",
        data=json.dumps(
            {
                "data": {
                    "type": "articles",
                    "id": "2",
                    "attributes": {"title": "New title", "content": "New content"},
                }
            }
        ),
        content_type="application/vnd.api+json",
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
            "type": "articles",
        },
        "links": {"self": "/articles/1"},
    }

    article.refresh_from_db()
    assert (article.title, article.content) == ("New title", "Test content")


@pytest.mark.django_db
def test_edit_one_no_fields(article: ArticleModel, client: django.test.Client):
    response = client.patch(
        f"/articles/{article.id}",
        data=json.dumps(
            {"data": {"type": "articles", "id": str(article.id), "attributes": {}}}
        ),
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": [
            {
                "status": "400",
                "code": "bad_request",
                "title": "Bad request",
                "detail": "At least one attribute must be set",
                "source": {"pointer": "/data/attributes"},
            }
        ],
    }


@pytest.mark.django_db
def test_edit_one_validation_error(article: ArticleModel, client: django.test.Client):
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
        "errors": [
            {
                "status": "400",
                "code": "bad_request",
                "title": "string_type",
                "detail": "Input should be a valid string",
                "source": {"pointer": "/attributes/title"},
            }
        ],
    }


@pytest.mark.django_db
def test_edit_one_extra_fields(article: ArticleModel, client: django.test.Client):
    response = client.patch(
        f"/articles/{article.id}",
        data=json.dumps(
            {
                "data": {
                    "type": "articles",
                    "id": str(article.id),
                    "attributes": {
                        "title": "New title",
                        "content": "New content",
                        "age": 3,
                    },
                }
            }
        ),
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 400, response.json()
    assert response.json() == {
        "errors": [
            {
                "status": "400",
                "code": "bad_request",
                "title": "extra_forbidden",
                "detail": "Extra inputs are not permitted",
                "source": {"pointer": "/attributes/age"},
            }
        ],
    }


@pytest.mark.django_db
def test_delete_one_article(article: ArticleModel, client: django.test.Client):
    response = client.delete(f"/articles/{article.id}")
    assert response.status_code == 204
    assert response.content == b""
    assert not ArticleModel.objects.filter(id=article.id).exists()


@pytest.mark.django_db
def test_delete_one_article_not_found(client: django.test.Client):
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


@pytest.mark.django_db
def test_get_many(article: ArticleModel, client: django.test.Client):
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
