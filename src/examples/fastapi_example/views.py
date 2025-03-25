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
    def edit_one(cls, obj: ArticleSchema) -> Response:
        if not obj.attributes.model_fields_set:
            raise pjst_exceptions.BadRequest("At least one attribute must be set")
        with Session(engine) as session:
            try:
                article = session.scalars(
                    select(ArticleModel).where(ArticleModel.id == obj.id)
                ).one()
            except NoResultFound:
                raise pjst_exceptions.NotFound(f"Article with id '{obj.id}' not found")
            if "title" in obj.attributes.model_fields_set:
                article.title = obj.attributes.title
            if "content" in obj.attributes.model_fields_set:
                article.content = obj.attributes.content
            session.commit()
            session.refresh(article)
        return Response(data=article)

    @classmethod
    def serialize(cls, obj: ArticleModel) -> ArticleSchema:
        return ArticleSchema(
            id=str(obj.id),
            attributes=ArticleSchema.Attributes(title=obj.title, content=obj.content),
        )
