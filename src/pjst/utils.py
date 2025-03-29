import inspect
import typing

if typing.TYPE_CHECKING:
    from pjst.resource_handler import ResourceHandler


def hasdirectattr(cls: "type[ResourceHandler]", method: str) -> bool:
    try:
        attr = getattr(cls, method)
        name = attr.__qualname__
        return name[: len(cls.__name__)] == cls.__name__
    except AttributeError:  # pragma: no cover
        return False


def find_annotations(func, cls):
    signature = inspect.signature(func)
    return [
        key for key, value in signature.parameters.items() if value.annotation == cls
    ]
