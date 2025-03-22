# Todos

- [ ] Request object with data injection
- [ ] Sample flask app
- [ ] Sample fastapi app

# Usage

```python
# Django

## views.py (django)

from pjst import Resource, Response, Serialized
from pjst import exceptions as pjst_exceptions

from .models import Article as ArticleModel


class ArticleResource(Resource):
    TYPE = "articles"

    @classmethod
    def get_one(cls, article_id: str) -> Response:
        try:
            return {"data": ArticleModel.objects.get(id=article_id)}
        except ArticleModel.DoesNotExist:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def serialize(cls, article: ArticleModel) -> Serialized:
        return {"attributes": {"title": article.title, "content": article.content}}


## urls.py (django)

from pjst.django import register

from .views import ArticleResource

urlpatterns = [
    *register(ArticleResource),
]


# flask + sqlmodel

## app.py

from flask import Flask
from pjst import Resource, Response, Serialized
from pjst import exceptions as pjst_exceptions
from pjst.flask import register
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session

from .database import engine
from .models import Article as ArticleModel


class ArticleResource(Resource):
    TYPE = "articles"

    @classmethod
    def get_one(cls, article_id: str) -> Response:
        with Session(engine) as session:
            try:
                article = (
                    session.exec(ArticleModel)
                    .where(ArticleModel.id == article_id)
                    .one()
                )
            except NoResultFound:
                raise pjst_exceptions.NotFound("Article not found")
        return {"data": article}

    @classmethod
    def serialize(cls, article: ArticleModel) -> Serialized:
        return {"attributes": {"title": article.title, "content": article.content}}


app = Flask(__name__)
register(app, ArticleResource)


# Fastapi + sqlmodel

## app.py

from fastapi import Depends
from fastapi import FastAPI
from pjst import Resource, Response, Serialized
from pjst import exceptions as pjst_exceptions
from pjst.fastapi import register
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import Session

from .database import engine
from .models import Article as ArticleModel


def get_session():
    with Session(engine) as session:
        yield session


class ArticleResource(Resource):
    TYPE = "articles"

    @classmethod
    def get_one(
        cls,
        article_id: str,
        session: Session = Depends(get_session),
    ) -> Response:
        try:
            article = (
                session.exec(ArticleModel).where(ArticleModel.id == article_id).one()
            )
        except NoResultFound:
            raise pjst_exceptions.NotFound("Article not found")
        return {"data": article}

    @classmethod
    def serialize(cls, article: ArticleModel) -> Serialized:
        return {"attributes": {"title": article.title, "content": article.content}}


app = FastAPI()
register(app, ArticleResource)
```

```
