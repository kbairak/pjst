import datetime

from flask import Flask
from sqlalchemy.exc import NoResultFound
from sqlmodel import Field, Session, SQLModel, create_engine, select

from pjst import exceptions as pjst_exceptions
from pjst.flask import register
from pjst.resource import ResourceHandler
from pjst.types import Resource, Response


class Article(SQLModel, table=True):
    __tablename__ = "articles_app_article"

    id: int = Field(primary_key=True)
    title: str
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


engine = create_engine("sqlite:///src/examples/db.sqlite3")


app = Flask(__name__)


class ArticleResource(ResourceHandler):
    TYPE = "articles"

    @classmethod
    def get_one(cls, obj_id: str) -> Response:
        try:
            with Session(engine) as session:
                article = session.exec(
                    select(Article).where(Article.id == obj_id)
                ).one()
            return Response(data=article)
        except NoResultFound:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def serialize(cls, obj: Article) -> Resource:
        return Resource(
            id=str(obj.id), attributes={"title": obj.title, "content": obj.content}
        )


register(app, ArticleResource)
