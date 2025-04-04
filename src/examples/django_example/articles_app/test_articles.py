import json
from typing import Callable

import django.test
import pytest

from .models import ArticleModel


@pytest.fixture()
def get_articles() -> Callable[[int], list[ArticleModel]]:
    def fn(count: int) -> list[ArticleModel]:
        return ArticleModel.objects.bulk_create(
            [
                ArticleModel(title=f"Test title {i}", content=f"Test content {i}")
                for i in range(1, count + 1)
            ]
        )

    return fn


@pytest.fixture()
def article(get_articles: Callable[[int], list[ArticleModel]]) -> ArticleModel:
    return get_articles(1)[0]


@pytest.mark.django_db
def test_get_one(article: ArticleModel, client: django.test.Client):
    response = client.get(f"/articles/{article.id}")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "type": "articles",
            "id": "1",
            "attributes": {"title": "Test title 1", "content": "Test content 1"},
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
            "attributes": {"title": "New title", "content": "Test content 1"},
            "id": "1",
            "links": {"self": "/articles/1"},
            "type": "articles",
        },
        "links": {"self": "/articles/1"},
    }

    article.refresh_from_db()
    assert (article.title, article.content) == ("New title", "Test content 1")


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
def test_get_many(
    get_articles: Callable[[int], list[ArticleModel]], client: django.test.Client
):
    articles = get_articles(2)
    response = client.get("/articles")
    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "type": "articles",
                "id": str(article.id),
                "attributes": {"title": article.title, "content": article.content},
                "links": {"self": f"/articles/{article.id}"},
            }
            for article in articles
        ],
        "links": {"self": "/articles"},
    }


@pytest.mark.django_db
def test_get_many_with_filter(
    get_articles: Callable[[int], list[ArticleModel]], client: django.test.Client
):
    articles = get_articles(2)
    response = client.get("/articles", {"filter[title]": articles[0].title})
    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "type": "articles",
                "id": str(articles[0].id),
                "attributes": {
                    "title": articles[0].title,
                    "content": articles[0].content,
                },
                "links": {"self": f"/articles/{articles[0].id}"},
            }
        ],
        "links": {"self": "/articles"},
    }
