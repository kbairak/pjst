from typing import cast

from django import http as django_http
from django.urls import URLPattern, path, reverse

from . import exceptions as pjst_exceptions
from . import types as pjst_types
from .resource_handler import ResourceHandler
from .utils import hasdirectattr


def register(resource_cls: type[ResourceHandler]) -> list[URLPattern]:
    result = []

    def _one_view(
        request: django_http.HttpRequest, obj_id: str
    ) -> django_http.HttpResponse:
        try:
            simple_response = resource_cls._handle_one(request, request.body, obj_id)
            if request.method == "DELETE" and simple_response is None:
                return django_http.HttpResponse("", status=204)
        except pjst_exceptions.PjstException as exc:
            result = django_http.JsonResponse(
                pjst_types.Document(errors=exc.render()).model_dump(exclude_unset=True),
                status=exc.status,
            )
            result["Content-Type"] = "application/vnd.api+json"
            return result
        if not isinstance(simple_response, pjst_types.Response):
            return simple_response
        processed_response = resource_cls._postprocess_one(simple_response)
        assert isinstance(processed_response.data, pjst_types.Resource)
        self_link = reverse(
            f"{resource_cls.TYPE}_object", kwargs={"obj_id": processed_response.data.id}
        )
        if "self" not in processed_response.links:
            processed_response.links = {**processed_response.links, "self": self_link}
        assert isinstance(processed_response.data, pjst_types.Resource)
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

    if (
        hasdirectattr(resource_cls, "get_one")
        or hasdirectattr(resource_cls, "edit_one")
        or hasdirectattr(resource_cls, "delete_one")
    ):
        result.append(
            path(
                f"{resource_cls.TYPE}/<str:obj_id>",
                _one_view,
                name=f"{resource_cls.TYPE}_object",
            )
        )

    def _many_view(request: django_http.HttpRequest) -> django_http.HttpResponse:
        try:
            if request.method == "GET":
                kwargs = resource_cls._process_filters(request.GET)
                simple_response = resource_cls.get_many(**kwargs)
            else:  # pragma: no cover
                raise pjst_exceptions.MethodNotAllowed(
                    f"Method {request.method} not allowed"
                )
        except pjst_exceptions.PjstException as exc:
            result = django_http.JsonResponse(
                pjst_types.Document(errors=exc.render()).model_dump(exclude_unset=True),
                status=exc.status,
            )
            result["Content-Type"] = "application/vnd.api+json"
            return result
        if not isinstance(simple_response, pjst_types.Response):
            return simple_response
        processed_response = resource_cls._postprocess_many(simple_response)
        processed_response.data = cast(
            list[pjst_types.Resource], processed_response.data
        )
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

    if hasdirectattr(resource_cls, "get_many"):
        result.append(
            path(
                resource_cls.TYPE,
                _many_view,
                name=f"{resource_cls.TYPE}_list",
            )
        )

    return result
