from typing import Any

import pydantic

from pjst.exceptions import (
    BadRequest,
    convert_pydantic_validationerror_to_pjst_badrequest,
)

from .types import Document, Resource, Response


class ResourceHandler:
    TYPE: str

    @classmethod
    def get_one(cls, obj_id: str) -> Any:
        raise NotImplementedError()

    @classmethod
    def edit_one(cls, obj: Any) -> Any:
        raise NotImplementedError()

    @classmethod
    def serialize(cls, obj: Any) -> Any:
        raise NotImplementedError()

    @classmethod
    def _postprocess_one(cls, simple_response: Response) -> Document:
        serialized_object = cls.serialize(simple_response.data)
        serialized_object.type = cls.TYPE
        return Document(data=serialized_object, links=simple_response.links)

    @classmethod
    def _process_body(cls, body_raw: Any, annotation: type) -> Any:
        try:
            if isinstance(body_raw, (str, bytes)):
                body = Document.model_validate_json(body_raw)
            else:
                body = Document.model_validate(body_raw)
        except pydantic.ValidationError as exc:
            raise convert_pydantic_validationerror_to_pjst_badrequest(exc)
        if not isinstance(body.data, Resource):
            raise BadRequest("Invalid data field", source={"pointer": "/data"})
        if issubclass(annotation, pydantic.BaseModel):
            try:
                return annotation.model_validate(body.data.model_dump())
            except pydantic.ValidationError as exc:
                raise convert_pydantic_validationerror_to_pjst_badrequest(exc)
        else:
            return body.data
