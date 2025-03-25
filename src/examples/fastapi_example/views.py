from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from pjst import exceptions as pjst_exceptions
from pjst.resource import ResourceHandler
from pjst.types import Resource, Response

from .models import ArticleModel, engine


class ArticleSchema(Resource):
    class Attributes(BaseModel):
        title: str = Field(default="", examples=["Title"])
        content: str = Field(default="", examples=["Content"])

    type: str = Field(default="articles")
    id: str = Field(default="1", examples=["1"])
    attributes: Attributes = Field(default_factory=Attributes)
    links: dict[str, str] = Field(
        default_factory=dict, examples=[{"self": "/articles/1"}]
    )


class ArticleResourceHandler(ResourceHandler):
    TYPE = "articles"

    @classmethod
    def get_one(cls, obj_id: str) -> Response:
        try:
            with Session(engine) as session:
                article = session.scalars(
                    select(ArticleModel).where(ArticleModel.id == obj_id)
                ).one()
            return Response(data=article)
        except NoResultFound:
            raise pjst_exceptions.NotFound("ArticleSchema not found")

    @classmethod
    def serialize(cls, obj: ArticleModel) -> ArticleSchema:
        return ArticleSchema(
            id=str(obj.id),
            attributes=ArticleSchema.Attributes(title=obj.title, content=obj.content),
        )
