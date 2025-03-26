from typing import Any

import pydantic

from pjst import exceptions as pjst_exceptions

from . import types as pjst_types


class ResourceHandler:
    TYPE: str

    @classmethod
    def get_one(cls, obj_id: str, *args, **kwargs) -> Any:  # pragma: no cover
        raise NotImplementedError()

    @classmethod
    def edit_one(cls, obj: Any) -> Any:  # pragma: no cover
        raise NotImplementedError()

    @classmethod
    def delete_one(cls, obj_id: str) -> None:  # pragma: no cover
        raise NotImplementedError()

    @classmethod
    def serialize(cls, obj: Any) -> Any:  # pragma: no cover
        raise NotImplementedError()

    @classmethod
    def _postprocess_one(
        cls, simple_response: pjst_types.Response
    ) -> pjst_types.Document:
        serialized_object = cls.serialize(simple_response.data)
        serialized_object.type = cls.TYPE
        return pjst_types.Document(data=serialized_object, links=simple_response.links)

    @classmethod
    def _process_body(cls, body_raw: Any, annotation: type) -> Any:
        try:
            if isinstance(body_raw, (str, bytes)):
                body = pjst_types.Document.model_validate_json(body_raw)
            else:
                body = pjst_types.Document.model_validate(body_raw)
        except pydantic.ValidationError as exc:
            raise pjst_exceptions.convert_pydantic_validationerror_to_pjst_badrequest(
                exc
            )
        if not isinstance(body.data, pjst_types.Resource):
            raise pjst_exceptions.BadRequest(
                "Invalid data field", source={"pointer": "/data"}
            )
        if issubclass(annotation, pydantic.BaseModel):
            try:
                return annotation.model_validate(
                    body.data.model_dump(exclude_unset=True)
                )
            except pydantic.ValidationError as exc:
                raise pjst_exceptions.convert_pydantic_validationerror_to_pjst_badrequest(
                    exc
                )
        else:  # pragma: no cover
            return body.data
