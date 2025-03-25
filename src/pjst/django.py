import inspect
from typing import Callable

from django import http as django_http
from django.urls import URLPattern, path, reverse

from pjst import exceptions as pjst_exceptions
from pjst.types import Document, Resource, Response

from .resource import ResourceHandler
from .utils import hasdirectattr


def _one_view_factory(
    resource_cls: type[ResourceHandler],
) -> Callable[..., django_http.HttpResponse]:
    def _one_view(
        request: django_http.HttpRequest, obj_id: str
    ) -> django_http.HttpResponse:
        try:
            if request.method == "GET":
                simple_response = resource_cls.get_one(obj_id)
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
                simple_response = resource_cls.edit_one(obj)
            else:
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


def register(resource_cls: type[ResourceHandler]) -> list[URLPattern]:
    result = []
    if hasdirectattr(resource_cls, "get_one") or hasdirectattr(
        resource_cls, "edit_one"
    ):
        result.append(
            path(
                f"{resource_cls.TYPE}/<str:obj_id>",
                _one_view_factory(resource_cls),
                name=f"{resource_cls.TYPE}_object",
            )
        )
    return result
