from pydantic import BaseModel, Field

from pjst import ResourceHandler
from pjst import exceptions as pjst_exceptions
from pjst.types import Resource, Response

from .models import Article as ArticleModel


class Article(Resource):
    class Attributes(BaseModel):
        title: str = Field(default="", examples=["Title"])
        content: str = Field(default="", examples=["Content"])

    type: str = Field(default="articles")
    id: str = Field(default="1", examples=["1"])
    attributes: Attributes = Field(default_factory=Attributes)
    links: dict[str, str] = Field(
        default_factory=dict, examples=[{"self": "/articles/1"}]
    )


class ArticleResource(ResourceHandler):
    TYPE = "articles"

    @classmethod
    def get_one(cls, obj_id: str) -> Response:
        try:
            return Response(data=ArticleModel.objects.get(id=obj_id))
        except ArticleModel.DoesNotExist:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def serialize(cls, obj: ArticleModel) -> Article:
        return Article(
            id=str(obj.id),
            attributes=Article.Attributes(title=obj.title, content=obj.content),
        )
