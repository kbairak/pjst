import inspect
from typing import Callable, cast

from django import http as django_http
from django.urls import URLPattern, path, reverse

from pjst import exceptions as pjst_exceptions
from pjst.types import Document, Resource, Response

from .resource_handler import ResourceHandler
from .utils import find_annotations, hasdirectattr


def _one_view_factory(
    resource_cls: type[ResourceHandler],
) -> Callable[..., django_http.HttpResponse]:
    def _one_view(
        request: django_http.HttpRequest, obj_id: str
    ) -> django_http.HttpResponse:
        try:
            if request.method == "GET":
                request_parameters = find_annotations(
                    resource_cls.get_one, django_http.HttpRequest
                )
                simple_response = resource_cls.get_one(
                    obj_id, **{key: request for key in request_parameters}
                )
            elif request.method == "PATCH":
                obj = resource_cls._process_body(
                    request.body,
                    inspect.signature(resource_cls.edit_one)
                    .parameters["obj"]
                    .annotation,
                )
                if isinstance(obj, Resource) and obj.id != obj_id:
                    raise pjst_exceptions.BadRequest(
                        f"ID in URL ({obj_id}) does not match ID in body ({obj.id})"
                    )
                request_parameters = find_annotations(
                    resource_cls.edit_one, django_http.HttpRequest
                )
                simple_response = resource_cls.edit_one(
                    obj, **{key: request for key in request_parameters}
                )
            elif request.method == "DELETE":
                request_parameters = find_annotations(
                    resource_cls.delete_one, django_http.HttpRequest
                )
                simple_response = resource_cls.delete_one(
                    obj_id, **{key: request for key in request_parameters}
                )
                if simple_response is None:
                    return django_http.HttpResponse("", status=204)
            else:  # pragma: no cover
                raise pjst_exceptions.MethodNotAllowed(
                    f"Method {request.method} not allowed"
                )
        except pjst_exceptions.PjstException as exc:
            result = django_http.JsonResponse(
                Document(errors=exc.render()).model_dump(exclude_unset=True),
                status=exc.status,
            )
            result["Content-Type"] = "application/vnd.api+json"
            return result
        if not isinstance(simple_response, Response):
            return simple_response
        processed_response = resource_cls._postprocess_one(simple_response)
        assert isinstance(processed_response.data, Resource)
        self_link = reverse(
            f"{resource_cls.TYPE}_object", kwargs={"obj_id": processed_response.data.id}
        )
        if "self" not in processed_response.links:
            processed_response.links = {**processed_response.links, "self": self_link}
        assert isinstance(processed_response.data, Resource)
        if "self" not in processed_response.data.links:
            processed_response.data.links = {
                **processed_response.data.links,
                "self": self_link,
            }
        result = django_http.JsonResponse(
            processed_response.model_dump(exclude_unset=True)
        )
        result["Content-Type"] = "application/vnd.api+json"
        return result

    return _one_view


def _many_view_factory(
    resource_cls: type[ResourceHandler],
) -> Callable[..., django_http.HttpResponse]:
    def _many_view(request: django_http.HttpRequest) -> django_http.HttpResponse:
        try:
            if request.method == "GET":
                simple_response = resource_cls.get_many()
            else:  # pragma: no cover
                raise pjst_exceptions.MethodNotAllowed(
                    f"Method {request.method} not allowed"
                )
        except pjst_exceptions.PjstException as exc:
            result = django_http.JsonResponse(
                Document(errors=exc.render()).model_dump(exclude_unset=True),
                status=exc.status,
            )
            result["Content-Type"] = "application/vnd.api+json"
            return result
        if not isinstance(simple_response, Response):
            return simple_response
        processed_response = resource_cls._postprocess_many(simple_response)
        processed_response.data = cast(list[Resource], processed_response.data)
        if "self" not in processed_response.links:
            processed_response.links = {
                **processed_response.links,
                "self": reverse(f"{resource_cls.TYPE}_list"),
            }
        for obj in processed_response.data:
            if "self" not in obj.links:
                obj.links = {
                    **obj.links,
                    "self": reverse(
                        f"{resource_cls.TYPE}_object", kwargs={"obj_id": obj.id}
                    ),
                }
        result = django_http.JsonResponse(
            processed_response.model_dump(exclude_unset=True)
        )
        result["Content-Type"] = "application/vnd.api+json"
        return result

    return _many_view


def register(resource_cls: type[ResourceHandler]) -> list[URLPattern]:
    result = []
    if (
        hasdirectattr(resource_cls, "get_one")
        or hasdirectattr(resource_cls, "edit_one")
        or hasdirectattr(resource_cls, "delete_one")
    ):
        result.append(
            path(
                f"{resource_cls.TYPE}/<str:obj_id>",
                _one_view_factory(resource_cls),
                name=f"{resource_cls.TYPE}_object",
            )
        )

    if hasdirectattr(resource_cls, "get_many"):
        result.append(
            path(
                resource_cls.TYPE,
                _many_view_factory(resource_cls),
                name=f"{resource_cls.TYPE}_list",
            )
        )

    return result
