from typing import Any

from pydantic import BaseModel, Field


class ResourceIdentifier(BaseModel):
    type: str = Field(default="", examples=["type"])
    id: str = Field(default="", examples=["id"])


class Relationship(BaseModel):
    data: ResourceIdentifier | list[ResourceIdentifier] | None = Field(
        default_factory=lambda: None,
        examples=[
            ResourceIdentifier(type="type", id="id"),
            [ResourceIdentifier(type="type", id="id")],
        ],
    )
    links: dict[str, str] = Field(
        default_factory=dict,
        examples=[{"self": "relationship_link", "related": "related_link"}],
    )


class Resource(ResourceIdentifier):
    attributes: Any = None
    relationships: dict[str, Relationship] = Field(default_factory=dict, examples=[{}])
    links: dict[str, str] = Field(
        default_factory=dict, examples=[{"self": "self_link"}]
    )


class Error(BaseModel):
    status: str
    code: str
    title: str
    detail: str
    source: dict | None = None


class Document(BaseModel):
    data: Resource | list[Resource] | None = None
    errors: list[Error] | None = None
    links: dict[str, str] = Field(default_factory=dict)


class Response(BaseModel):
    data: Any
    links: dict[str, str] = Field(default_factory=dict)
