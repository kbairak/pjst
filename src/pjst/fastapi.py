import inspect

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pjst.resource import ResourceHandler
from pjst.types import Resource, Response


class JsonApiResponse(JSONResponse):
    media_type = "application/vnd.api+json"


def register(app: FastAPI, resource_cls: type[ResourceHandler]) -> None:
    def _get_one(obj_id: str, request: Request) -> JsonApiResponse:
        simple_response = resource_cls.get_one(obj_id)
        if not isinstance(simple_response, Response):
            return simple_response
        processed_response = resource_cls._process_one(simple_response)
        if "links" not in processed_response.links:
            processed_response.links["self"] = request.url.path
        assert isinstance(processed_response.data, Resource)
        if "links" not in processed_response.data.links:
            processed_response.data.links["self"] = request.url.path
        return JsonApiResponse(processed_response.model_dump())

    app.get(
        f"/{resource_cls.TYPE}/{{obj_id}}",
        response_model=inspect.signature(resource_cls.serialize).return_annotation,
    )(_get_one)
