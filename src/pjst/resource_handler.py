import inspect
from typing import Any, Mapping

import pydantic

from . import exceptions as pjst_exceptions
from . import types as pjst_types
from .utils import find_annotations


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
    def get_many(cls) -> pjst_types.Response:
        raise NotImplementedError()

    @classmethod
    def serialize(cls, obj: Any) -> Any:  # pragma: no cover
        raise NotImplementedError()

    @classmethod
    def _handle_one(cls, request, request_body, obj_id: str) -> Any:
        if request.method == "GET":
            request_parameters = find_annotations(cls.get_one, type(request))
            simple_response = cls.get_one(
                obj_id, **{key: request for key in request_parameters}
            )
        elif request.method == "PATCH":
            obj = cls._process_body(
                request_body,
                inspect.signature(cls.edit_one).parameters["obj"].annotation,
            )
            if isinstance(obj, pjst_types.Resource) and obj.id != obj_id:
                raise pjst_exceptions.BadRequest(
                    f"ID in URL ({obj_id}) does not match ID in body ({obj.id})"
                )
            request_parameters = find_annotations(cls.edit_one, type(request))
            simple_response = cls.edit_one(
                obj, **{key: request for key in request_parameters}
            )
        elif request.method == "DELETE":
            request_parameters = find_annotations(cls.delete_one, type(request))
            simple_response = cls.delete_one(
                obj_id, **{key: request for key in request_parameters}
            )
        else:  # pragma: no cover
            raise pjst_exceptions.MethodNotAllowed(
                f"Method {request.method} not allowed"
            )
        return simple_response

    @classmethod
    def _postprocess_one(
        cls, simple_response: pjst_types.Response
    ) -> pjst_types.Document:
        serialized_object = cls.serialize(simple_response.data)
        serialized_object.type = cls.TYPE
        return pjst_types.Document(data=serialized_object, links=simple_response.links)

    @classmethod
    def _postprocess_many(
        cls, simple_response: pjst_types.Response
    ) -> pjst_types.Document:
        serialized_list = []
        for obj in simple_response.data:
            serialized_list.append(cls.serialize(obj))
            serialized_list[-1].type = cls.TYPE
        return pjst_types.Document(data=serialized_list, links=simple_response.links)

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

    @classmethod
    def _process_filters(cls, query_params: Mapping[str, str]) -> dict[str, str]:
        signature = inspect.signature(cls.get_many)
        kwargs = {}
        errors = []
        for key, value in signature.parameters.items():
            if isinstance(value.default, pjst_types._Filter):
                try:
                    kwargs[key] = query_params[f"filter[{key}]"]
                except KeyError:
                    try:
                        types = value.annotation.__args__
                    except AttributeError:
                        types = [value.annotation]
                    if type(None) in types:
                        kwargs[key] = None
                    else:
                        errors.append(
                            pjst_exceptions.BadRequest(
                                f"Parameter 'filter[{key}]' is required"
                            )
                        )
        if errors:
            raise pjst_exceptions.PjstExceptionMulti(*errors)
        return kwargs
