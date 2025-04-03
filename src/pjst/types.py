from typing import Any

import pydantic


class ResourceIdentifier(pydantic.BaseModel):
    type: str = pydantic.Field(default="", examples=["type"])
    id: str = pydantic.Field(default="", examples=["id"])


class Relationship(pydantic.BaseModel):
    data: ResourceIdentifier | list[ResourceIdentifier] | None = pydantic.Field(
        default_factory=lambda: None,
        examples=[
            ResourceIdentifier(type="type", id="id"),
            [ResourceIdentifier(type="type", id="id")],
        ],
    )
    links: dict[str, str] = pydantic.Field(
        default_factory=dict,
        examples=[{"self": "relationship_link", "related": "related_link"}],
    )


class Resource(ResourceIdentifier):
    attributes: Any = None
    relationships: dict[str, Relationship] = pydantic.Field(
        default_factory=dict, examples=[{}]
    )
    links: dict[str, str] = pydantic.Field(
        default_factory=dict, examples=[{"self": "self_link"}]
    )


class Error(pydantic.BaseModel):
    status: str
    code: str
    title: str
    detail: str
    source: dict | None = None


class Document(pydantic.BaseModel):
    data: Resource | list[Resource] | None = None
    errors: list[Error] | None = None
    links: dict[str, str] = pydantic.Field(default_factory=dict)


class Response(pydantic.BaseModel):
    data: Any
    links: dict[str, str] = pydantic.Field(default_factory=dict)


class Filter:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
