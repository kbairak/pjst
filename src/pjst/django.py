from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import URLPattern, path, reverse

from pjst.types import Resource

from .resource import ResourceHandler


def hasdirectattr(cls: type[ResourceHandler], method: str) -> bool:
    try:
        attr = getattr(cls, method)
        name = attr.__qualname__
        return name[: len(cls.__name__)] == cls.__name__
    except AttributeError:
        return False


def _get_one(
    resource_cls: type[ResourceHandler],
) -> Callable[[HttpRequest, str], HttpResponse]:
    def view(request: HttpRequest, obj_id: str) -> HttpResponse:
        simple_response = resource_cls.get_one(obj_id)
        if isinstance(simple_response, HttpResponse):
            return simple_response
        processed_response = resource_cls._process_one(simple_response)
        if "links" not in processed_response.links:
            processed_response.links["self"] = reverse(
                f"{resource_cls.TYPE}_object", kwargs={"obj_id": obj_id}
            )
        assert isinstance(processed_response.data, Resource)
        if "links" not in processed_response.data.links:
            processed_response.data.links["self"] = reverse(
                f"{resource_cls.TYPE}_object", kwargs={"obj_id": obj_id}
            )
        result = JsonResponse(processed_response.model_dump())
        result["Content-Type"] = "application/vnd.api+json"
        return result

    return view


def register(resource_cls: type[ResourceHandler]) -> list[URLPattern]:
    result = []
    if hasdirectattr(resource_cls, "get_one"):
        result.append(
            path(
                f"{resource_cls.TYPE}/<str:obj_id>/",
                _get_one(resource_cls),
                name=f"{resource_cls.TYPE}_object",
            )
        )
    return result
