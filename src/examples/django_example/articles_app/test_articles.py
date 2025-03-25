import django.test
import pytest

from .models import ArticleModel


@pytest.mark.django_db
def test_get_article(client: django.test.Client):
    article = ArticleModel.objects.create(title="Test", content="Test")
    response = client.get(f"/articles/{article.id}")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "type": "articles",
            "id": "1",
            "attributes": {"title": "Test", "content": "Test"},
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
