import datetime

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic import Field as PydanticField
from sqlalchemy.exc import NoResultFound
from sqlmodel import Field as SQLModelField
from sqlmodel import Session, SQLModel, create_engine, select

from pjst import exceptions as pjst_exceptions
from pjst.fastapi import register
from pjst.resource import ResourceHandler
from pjst.types import Resource, Response


class ArticleModel(SQLModel, table=True):
    __tablename__ = "articles_app_article"

    id: int = SQLModelField(primary_key=True)
    title: str
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


engine = create_engine("sqlite:///src/examples/db.sqlite3")

app = FastAPI()


class Article(Resource):
    class Attributes(BaseModel):
        title: str = PydanticField(default="", examples=["Title"])
        content: str = PydanticField(default="", examples=["Content"])

    type: str = PydanticField(default="articles")
    id: str = PydanticField(default="1", examples=["1"])
    attributes: Attributes = PydanticField(default_factory=Attributes)
    links: dict[str, str] = PydanticField(
        default_factory=dict, examples=[{"self": "/articles/1"}]
    )


class ArticleResource(ResourceHandler):
    TYPE = "articles"

    @classmethod
    def get_one(cls, obj_id: str) -> Response:
        try:
            with Session(engine) as session:
                article = session.exec(
                    select(ArticleModel).where(ArticleModel.id == obj_id)
                ).one()
            return Response(data=article)
        except NoResultFound:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def serialize(cls, obj: ArticleModel) -> Article:
        return Article(
            id=str(obj.id),
            attributes=Article.Attributes(title=obj.title, content=obj.content),
        )


register(app, ArticleResource)
