import inspect

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pjst import exceptions as pjst_exceptions
from pjst import types as pjst_types
from pjst.resource import ResourceHandler
from pjst.utils import hasdirectattr


class JsonApiResponse(JSONResponse):
    media_type = "application/vnd.api+json"


def register(app: FastAPI, resource_cls: type[ResourceHandler]) -> None:
    async def _one_view(obj_id: str, request: Request) -> JsonApiResponse:
        try:
            if request.method == "GET":
                simple_response = resource_cls.get_one(obj_id)
            elif request.method == "PATCH":
                obj = resource_cls._process_body(
                    await request.json(),
                    inspect.signature(resource_cls.edit_one)
                    .parameters["obj"]
                    .annotation,
                )
                if isinstance(obj, pjst_types.Resource) and obj.id != obj_id:
                    raise pjst_exceptions.BadRequest(
                        f"ID in URL ({obj_id}) does not match ID in body ({obj.id})"
                    )
                simple_response = resource_cls.edit_one(obj)
            else:
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
            response_model=inspect.signature(resource_cls.serialize).return_annotation,
        )(_one_view)

    if hasdirectattr(resource_cls, "edit_one"):
        app.patch(
            f"/{resource_cls.TYPE}/{{obj_id}}",
            response_model=inspect.signature(resource_cls.serialize).return_annotation,
        )(_one_view)
