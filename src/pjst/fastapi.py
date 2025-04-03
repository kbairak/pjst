import inspect
from typing import Annotated, cast

import fastapi
from fastapi.responses import JSONResponse
from pydantic import create_model

from pjst import exceptions as pjst_exceptions
from pjst import types as pjst_types
from pjst.resource_handler import ResourceHandler
from pjst.utils import hasdirectattr


class JsonApiResponse(JSONResponse):
    media_type = "application/vnd.api+json"


def register(app: fastapi.FastAPI, resource_cls: type[ResourceHandler]) -> None:
    if resource_type := inspect.signature(resource_cls.serialize).return_annotation:
        single_response_model = create_model(
            f"{resource_cls.TYPE}Response",
            __base__=pjst_types.Document,
            data=(resource_type, None),
        )
        collection_response_model = create_model(
            f"{resource_cls.TYPE}Response",
            __base__=pjst_types.Document,
            data=(list[resource_type], None),
        )
    else:
        single_response_model = collection_response_model = None

    async def _one_view(obj_id: str, request: fastapi.Request):
        try:
            simple_response = resource_cls._handle_one(
                request, await request.body(), obj_id
            )
            if request.method == "DELETE" and simple_response is None:
                return fastapi.Response("", status_code=204)
        except pjst_exceptions.PjstException as exc:
            return JsonApiResponse(
                pjst_types.Document(errors=exc.render()).model_dump(exclude_unset=True),
                status_code=exc.status,
            )
        if not isinstance(simple_response, pjst_types.Response):
            return simple_response
        processed_response = resource_cls._postprocess_one(simple_response)
        if "self" not in processed_response.links:
            processed_response.links = {
                **processed_response.links,
                "self": request.url.path,
            }
        assert isinstance(processed_response.data, pjst_types.Resource)
        if "self" not in processed_response.data.links:
            processed_response.data.links = {
                **processed_response.data.links,
                "self": request.url.path,
            }
        return JsonApiResponse(processed_response.model_dump(exclude_unset=True))

    if hasdirectattr(resource_cls, "get_one"):
        app.get(
            f"/{resource_cls.TYPE}/{{obj_id}}",
            name=f"Get {resource_cls.TYPE} object",
            response_model=single_response_model,
        )(_one_view)

    if hasdirectattr(resource_cls, "edit_one"):
        app.patch(
            f"/{resource_cls.TYPE}/{{obj_id}}",
            name=f"Edit {resource_cls.TYPE} object",
            response_model=single_response_model,
        )(_one_view)

    if hasdirectattr(resource_cls, "delete_one"):
        app.delete(
            f"/{resource_cls.TYPE}/{{obj_id}}",
            name=f"Delete {resource_cls.TYPE} object",
        )(_one_view)

    async def _many_view(**kwargs):
        request = kwargs["request"]
        try:
            if request.method == "GET":
                if "request" not in inspect.signature(resource_cls.get_many).parameters:
                    kwargs.pop("request")
                simple_response = resource_cls.get_many(**kwargs)
            else:  # pragma: no cover
                raise pjst_exceptions.MethodNotAllowed(
                    f"Method {request.method} not allowed"
                )
        except pjst_exceptions.PjstException as exc:
            return JsonApiResponse(
                pjst_types.Document(errors=exc.render()).model_dump(exclude_unset=True),
                status_code=exc.status,
            )
        if not isinstance(simple_response, pjst_types.Response):
            return simple_response
        processed_response = resource_cls._postprocess_many(simple_response)
        processed_response.data = cast(
            list[pjst_types.Resource], processed_response.data
        )
        if "self" not in processed_response.links:
            processed_response.links = {
                **processed_response.links,
                "self": request.url.path,
            }
        for obj in processed_response.data:
            if "self" not in obj.links:
                obj.links = {
                    **obj.links,
                    "self": app.url_path_for(
                        f"Get {resource_cls.TYPE} object", obj_id=obj.id
                    ),
                }
        return JsonApiResponse(processed_response.model_dump(exclude_unset=True))

    if hasdirectattr(resource_cls, "get_many"):
        parameters = [
            inspect.Parameter(
                "request",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=fastapi.Request,
            )
        ]
        for key, value in inspect.signature(resource_cls.get_many).parameters.items():
            if value.annotation is fastapi.Request:
                continue

            if (
                hasattr(value.annotation, "__origin__")
                and hasattr(value.annotation, "__metadata__")
                and len(value.annotation.__metadata__) == 1
                and isinstance(
                    metadata := value.annotation.__metadata__[0], pjst_types.Filter
                )
            ):
                parameters.append(
                    inspect.Parameter(
                        key,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=value.default,
                        annotation=Annotated[
                            value.annotation.__origin__,
                            fastapi.Query(alias=f"filter[{key}]", **metadata.kwargs),
                        ],
                    )
                )
            else:
                parameters.append(
                    inspect.Parameter(
                        key,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=value.default,
                        annotation=value.annotation,
                    )
                )

        _many_view.__signature__ = inspect.Signature(parameters)  # type: ignore

        app.get(
            f"/{resource_cls.TYPE}",
            name=f"Get {resource_cls.TYPE} collection",
            response_model=collection_response_model,
        )(_many_view)
