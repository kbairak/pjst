from flask import Flask, request

from pjst.resource import ResourceHandler
from pjst.types import Resource, Response


def register(app: Flask, resource_cls: type[ResourceHandler]) -> None:
    def _get_one(obj_id: str) -> tuple[dict, dict[str, str]]:
        simple_response = resource_cls.get_one(obj_id)
        if not isinstance(simple_response, Response):
            return simple_response
        processed_response = resource_cls._process_one(simple_response)
        if "links" not in processed_response.links:
            processed_response.links["self"] = request.path
        assert isinstance(processed_response.data, Resource)
        if "links" not in processed_response.data.links:
            processed_response.data.links["self"] = request.path
        return processed_response.model_dump(), {
            "Content-Type": "application/vnd.api+json"
        }

    app.route(f"/{resource_cls.TYPE}/<obj_id>")(_get_one)
