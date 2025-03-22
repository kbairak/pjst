from typing import Any

from .types import Document, Resource, Response


class ResourceHandler:
    TYPE: str

    @classmethod
    def get_one(cls, article_id: str) -> Response:
        raise NotImplementedError()

    @classmethod
    def serialize(cls, obj: Any) -> Resource:
        raise NotImplementedError()

    @classmethod
    def _process_one(cls, simple_response: Response) -> Document:
        serialized_object = cls.serialize(simple_response.data)
        serialized_object.type = cls.TYPE
        return Document(data=serialized_object, links=simple_response.links)
