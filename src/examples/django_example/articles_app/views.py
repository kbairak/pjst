from typing import Annotated

import pydantic

from pjst import ResourceHandler
from pjst import exceptions as pjst_exceptions
from pjst import types as pjst_types

from .models import ArticleModel


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
            return pjst_types.Response(data=ArticleModel.objects.get(id=obj_id))
        except ArticleModel.DoesNotExist:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def edit_one(cls, obj: ArticleSchema) -> pjst_types.Response:
        if not obj.attributes.model_fields_set:
            raise pjst_exceptions.BadRequest(
                "At least one attribute must be set",
                source={"pointer": "/data/attributes"},
            )
        try:
            article = ArticleModel.objects.get(id=obj.id)
        except ArticleModel.DoesNotExist:
            raise pjst_exceptions.NotFound(f"Article with id '{obj.id}' not found")
        if "title" in obj.attributes.model_fields_set:
            article.title = obj.attributes.title
        if "content" in obj.attributes.model_fields_set:
            article.content = obj.attributes.content
        article.save()
        return pjst_types.Response(data=article)

    @classmethod
    def delete_one(cls, obj_id: str) -> None:
        count, _ = ArticleModel.objects.filter(id=obj_id).delete()
        if count == 0:
            raise pjst_exceptions.NotFound(f"Article with id '{obj_id}' not found")

    @classmethod
    def get_many(
        cls,
        title: Annotated[str | None, pjst_types.Filter()] = None,
    ) -> pjst_types.Response:
        queryset = ArticleModel.objects.order_by("created_at")
        if title is not None:
            queryset = queryset.filter(title=title)
        return pjst_types.Response(data=queryset)

    @classmethod
    def serialize(cls, obj: ArticleModel) -> ArticleSchema:
        return ArticleSchema(
            id=str(obj.id),
            attributes=ArticleSchema.Attributes(title=obj.title, content=obj.content),
        )
