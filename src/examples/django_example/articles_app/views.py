from pjst import ResourceHandler
from pjst import exceptions as pjst_exceptions
from pjst.types import Resource, Response

from .models import Article as ArticleModel


class ArticleResource(ResourceHandler):
    TYPE = "articles"

    @classmethod
    def get_one(cls, obj_id: str) -> Response:
        try:
            return Response(data=ArticleModel.objects.get(id=obj_id))
        except ArticleModel.DoesNotExist:
            raise pjst_exceptions.NotFound("Article not found")

    @classmethod
    def serialize(cls, obj: ArticleModel) -> Resource:
        return Resource(
            id=str(obj.id), attributes={"title": obj.title, "content": obj.content}
        )
