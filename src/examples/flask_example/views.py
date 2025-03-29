import pydantic
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from pjst import exceptions as pjst_exceptions
from pjst import types as pjst_types
from pjst.resource_handler import ResourceHandler

from . import models


class ArticleSchema(pjst_types.Resource):
    class Attributes(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")

        title: str = pydantic.Field(default="", examples=["Title"])
        content: str = pydantic.Field(default="", examples=["Content"])

    type: str = pydantic.Field(default="articles")
    id: str = pydantic.Field(default="1", examples=["1"])
    attributes: Attributes = pydantic.Field(default_factory=Attributes)
    links: dict[str, str] = pydantic.Field(
        default_factory=dict, examples=[{"self": "/articles/1"}]
    )


class ArticleResourceHandler(ResourceHandler):
    TYPE = "articles"

    @classmethod
    def get_one(cls, obj_id: str) -> pjst_types.Response:
        try:
            with Session(models.engine) as session:
                article = session.scalars(
                    select(models.ArticleModel).where(models.ArticleModel.id == obj_id)
                ).one()
            return pjst_types.Response(data=article)
        except NoResultFound:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def edit_one(cls, obj: ArticleSchema) -> pjst_types.Response:
        if not obj.attributes.model_fields_set:
            raise pjst_exceptions.BadRequest(
                "At least one attribute must be set",
                source={"pointer": "/data/attributes"},
            )
        with Session(models.engine) as session:
            try:
                article = session.scalars(
                    select(models.ArticleModel).where(models.ArticleModel.id == obj.id)
                ).one()
            except NoResultFound:
                raise pjst_exceptions.NotFound(f"Article with id '{obj.id}' not found")
            if "title" in obj.attributes.model_fields_set:
                article.title = obj.attributes.title
            if "content" in obj.attributes.model_fields_set:
                article.content = obj.attributes.content
            session.commit()
            session.refresh(article)
        return pjst_types.Response(data=article)

    @classmethod
    def delete_one(cls, obj_id: str) -> None:
        with Session(models.engine) as session:
            try:
                article = session.scalars(
                    select(models.ArticleModel).where(models.ArticleModel.id == obj_id)
                ).one()
            except NoResultFound:
                raise pjst_exceptions.NotFound(f"Article with id '{obj_id}' not found")
            session.delete(article)
            session.commit()

    @classmethod
    def get_many(cls):
        with Session(models.engine) as session:
            try:
                articles = session.scalars(select(models.ArticleModel)).all()
            except NoResultFound:
                raise pjst_exceptions.NotFound("No articles found")
        return pjst_types.Response(data=articles)

    @classmethod
    def serialize(cls, obj: models.ArticleModel) -> ArticleSchema:
        return ArticleSchema(
            id=str(obj.id),
            attributes=ArticleSchema.Attributes(title=obj.title, content=obj.content),
        )
