from pjst.resource import ResourceHandler


def hasdirectattr(cls: type[ResourceHandler], method: str) -> bool:
    try:
        attr = getattr(cls, method)
        name = attr.__qualname__
        return name[: len(cls.__name__)] == cls.__name__
    except AttributeError:
        return False
