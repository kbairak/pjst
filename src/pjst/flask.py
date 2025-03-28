import inspect

import flask

from . import exceptions as pjst_exceptions
from . import types as pjst_types
from .resource_handler import ResourceHandler
from .utils import find_annotations, hasdirectattr


def register(app: flask.Flask, resource_cls: type[ResourceHandler]) -> None:
    def _one_view(
        obj_id: str,
    ) -> (
        tuple[dict, dict[str, str]] | tuple[dict, int, dict[str, str]] | tuple[str, int]
    ):
        try:
            if flask.request.method == "GET":
                request_parameters = find_annotations(
                    resource_cls.get_one, flask.Request
                )
                simple_response = resource_cls.get_one(
                    obj_id, **{key: flask.request for key in request_parameters}
                )
            elif flask.request.method == "PATCH":
                obj = resource_cls._process_body(
                    flask.request.json,
                    inspect.signature(resource_cls.edit_one)
                    .parameters["obj"]
                    .annotation,
                )
                if isinstance(obj, pjst_types.Resource) and obj.id != obj_id:
                    raise pjst_exceptions.BadRequest(
                        f"ID in URL ({obj_id}) does not match ID in body ({obj.id})"
                    )
                request_parameters = find_annotations(
                    resource_cls.edit_one, flask.Request
                )
                simple_response = resource_cls.edit_one(
                    obj, **{key: flask.request for key in request_parameters}
                )
            elif flask.request.method == "DELETE":
                request_parameters = find_annotations(
                    resource_cls.delete_one, flask.Request
                )
                simple_response = resource_cls.delete_one(
                    obj_id, **{key: flask.request for key in request_parameters}
                )
                if simple_response is None:
                    return "", 204
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
                "self": flask.request.path,
            }
        return processed_response.model_dump(exclude_unset=True), {
            "Content-Type": "application/vnd.api+json"
        }

    if (
        hasdirectattr(resource_cls, "get_one")
        or hasdirectattr(resource_cls, "edit_one")
        or hasdirectattr(resource_cls, "delete_one")
    ):
        app.route(f"/{resource_cls.TYPE}/<obj_id>", methods=["GET", "PATCH", "DELETE"])(
            _one_view
        )
