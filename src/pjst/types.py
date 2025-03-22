from typing import Any

from pydantic import BaseModel, Field


class ResourceIdentifier(BaseModel):
    type: str = Field(default="")
    id: str = Field(default="")


class Relationship(BaseModel):
    data: ResourceIdentifier | None = None
    links: dict[str, str] = Field(default_factory=dict)


class Resource(ResourceIdentifier):
    attributes: dict | None = None
    relationships: dict[str, Relationship] | None = None
    links: dict[str, str] = Field(default_factory=dict)


class Error(BaseModel):
    status: str
    code: str
    title: str
    detail: str


class Document(BaseModel):
    data: Resource | list[Resource] | None = None
    errors: list[Error] | None = None
    links: dict[str, str] = Field(default_factory=dict)


class Response(BaseModel):
    data: Any
    links: dict[str, str] = Field(default_factory=dict)
