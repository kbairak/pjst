import inspect
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import URLPattern, path, reverse

from pjst.exceptions import BadRequest, MethodNotAllowed, PjstException
from pjst.types import Document, Resource, Response

from .resource import ResourceHandler
from .utils import hasdirectattr


def _get_one_view(resource_cls: type[ResourceHandler]) -> Callable[..., HttpResponse]:
    def view(request: HttpRequest, **kwargs: str) -> HttpResponse:
        try:
            obj_id = kwargs["obj_id"]
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
                    raise BadRequest(
                        f"ID in URL ({obj_id}) does not match ID in body ({obj.id})"
                    )
                simple_response = resource_cls.edit_one(obj)
            else:
                raise MethodNotAllowed(f"Method {request.method} not allowed")
        except PjstException as exc:
            result = JsonResponse(
                Document(errors=exc.render()).model_dump(), status=exc.status
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
        if "links" not in processed_response.links:
            processed_response.links["self"] = self_link
        assert isinstance(processed_response.data, Resource)
        if "links" not in processed_response.data.links:
            processed_response.data.links["self"] = self_link
        result = JsonResponse(processed_response.model_dump())
        result["Content-Type"] = "application/vnd.api+json"
        return result

    return view


def register(resource_cls: type[ResourceHandler]) -> list[URLPattern]:
    result = []
    if hasdirectattr(resource_cls, "get_one") or hasdirectattr(
        resource_cls, "edit_one"
    ):
        result.append(
            path(
                f"{resource_cls.TYPE}/<str:obj_id>",
                _get_one_view(resource_cls),
                name=f"{resource_cls.TYPE}_object",
            )
        )
    return result
