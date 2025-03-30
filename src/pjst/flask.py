from typing import cast

import flask

from . import exceptions as pjst_exceptions
from . import types as pjst_types
from .resource_handler import ResourceHandler
from .utils import hasdirectattr


def register(app: flask.Flask, resource_cls: type[ResourceHandler]) -> None:
    def _one_view(
        obj_id: str,
    ) -> (
        tuple[dict, dict[str, str]] | tuple[dict, int, dict[str, str]] | tuple[str, int]
    ):
        try:
            simple_response = resource_cls._handle_one(
                flask.request, flask.request.get_json(silent=True), obj_id
            )
            if flask.request.method == "DELETE" and simple_response is None:
                return "", 204
        except pjst_exceptions.PjstException as exc:
            return (
                pjst_types.Document(errors=exc.render()).model_dump(exclude_unset=True),
                exc.status,
                {
                    "Content-Type": "application/vnd.api+json",
                },
            )
        if not isinstance(simple_response, pjst_types.Response):
            return simple_response
        processed_response = resource_cls._postprocess_one(simple_response)
        if "self" not in processed_response.links:
            processed_response.links = {
                **processed_response.links,
                "self": flask.request.path,
            }
        assert isinstance(processed_response.data, pjst_types.Resource)
        if "self" not in processed_response.data.links:
            processed_response.data.links = {
                **processed_response.data.links,
                "self": app.url_for(f"{resource_cls.TYPE}_object", obj_id=obj_id),
            }
        return processed_response.model_dump(exclude_unset=True), {
            "Content-Type": "application/vnd.api+json"
        }

    if (
        hasdirectattr(resource_cls, "get_one")
        or hasdirectattr(resource_cls, "edit_one")
        or hasdirectattr(resource_cls, "delete_one")
    ):
        app.add_url_rule(
            f"/{resource_cls.TYPE}/<obj_id>",
            f"{resource_cls.TYPE}_object",
            _one_view,
            methods=["GET", "PATCH", "DELETE"],
        )

    def _many_view():
        try:
            if flask.request.method == "GET":
                kwargs = resource_cls._process_filters(flask.request.args)
                simple_response = resource_cls.get_many(**kwargs)
            else:  # pragma: no cover
                raise pjst_exceptions.MethodNotAllowed(
                    f"Method {flask.request.method} not allowed"
                )
        except pjst_exceptions.PjstException as exc:
            return (
                pjst_types.Document(errors=exc.render()).model_dump(exclude_unset=True),
                exc.status,
                {
                    "Content-Type": "application/vnd.api+json",
                },
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
                "self": flask.request.path,
            }
        for obj in processed_response.data:
            if "self" not in obj.links:
                obj.links = {
                    **obj.links,
                    "self": app.url_for(f"{resource_cls.TYPE}_object", obj_id=obj.id),
                }
        return processed_response.model_dump(exclude_unset=True), {
            "Content-Type": "application/vnd.api+json"
        }

    if hasdirectattr(resource_cls, "get_many"):
        app.add_url_rule(
            f"/{resource_cls.TYPE}",
            f"{resource_cls.TYPE}_list",
            _many_view,
            methods=["GET"],
        )
