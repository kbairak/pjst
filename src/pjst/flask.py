import inspect

from flask import Flask, request

from . import exceptions as pjst_exceptions
from . import types as pjst_types
from .resource import ResourceHandler
from .utils import hasdirectattr


def register(app: Flask, resource_cls: type[ResourceHandler]) -> None:
    def _one_view(
        obj_id: str,
    ) -> tuple[dict, dict[str, str]] | tuple[dict, int, dict[str, str]]:
        try:
            if request.method == "GET":
                simple_response = resource_cls.get_one(obj_id)
            elif request.method == "PATCH":
                obj = resource_cls._process_body(
                    request.json,
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
            return (
                pjst_types.Document(errors=exc.render()).model_dump(),
                exc.status,
                {
                    "Content-Type": "application/vnd.api+json",
                },
            )
        if not isinstance(simple_response, pjst_types.Response):
            return simple_response
        processed_response = resource_cls._postprocess_one(simple_response)
        if "self" not in processed_response.links:
            processed_response.links["self"] = request.path
        assert isinstance(processed_response.data, pjst_types.Resource)
        if "self" not in processed_response.data.links:
            processed_response.data.links["self"] = request.path
        return processed_response.model_dump(), {
            "Content-Type": "application/vnd.api+json"
        }

    if hasdirectattr(resource_cls, "get_one") or hasdirectattr(
        resource_cls, "edit_one"
    ):
        app.route(f"/{resource_cls.TYPE}/<obj_id>", methods=["GET", "PATCH"])(_one_view)
