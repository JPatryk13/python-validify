from copy import deepcopy
import functools
from inspect import Parameter, Signature, getmro
from typing import Any

from .validator import describe_type, isvalid


class cls:
    @staticmethod
    def setattr_validate(__func, *, annotations: dict[str, Any]):

        @functools.wraps(__func)
        def wrapper(self, name, val):

            if name in annotations.keys():
                if not isvalid(val, annotations[name]):
                    raise TypeError(
                        f"Property `{name}` is not valid. Expected `{annotations[name]}`, "
                        f"got `{describe_type(annotations[name]).raw}`"
                    )

            return __func(self, name, val)

        return wrapper

    @staticmethod
    def validate(__class):
        _vars: dict[str, Any] = {}
        for m in getmro(__class):
            if m == object and "__setattr__" not in _vars.keys():
                # we want to capture setattr now just in case we have instance
                # properties to deal with later
                _vars["__setattr__"] = vars(m)["__setattr__"]
            else:
                # iterate over attributes of any other class and check if it's been
                # assigned to _vars which is meant to store anything that we want to
                # validate. In case of multiple attributes with the same name across
                # multiple classes the attribute that's been assigned first persists.
                # That ensures that overwritten (in child classes) attributes remain
                # in the most "up-to-date" version
                for attr in vars(m).items():
                    if attr[0] not in _vars.keys():
                        _vars.update([attr])
                    elif attr[0] == "__annotations__":
                        # annotations are treated similarly to atributes
                        for name, val in attr[1].items():
                            if name not in _vars["__annotations__"].keys():
                                _vars["__annotations__"][name] = val

        # print(pformat(_vars))

        for name, value in _vars.items():
            if name == "__setattr__" and "__annotations__" in _vars.keys():
                # it's default setter
                __class.__setattr__ = cls.setattr_validate(
                    __class.__setattr__, annotations=_vars["__annotations__"]
                )

            elif callable(value):
                # it's callable
                setattr(__class, name, func.validate(value))

            elif isinstance(value, classmethod):
                setattr(
                    __class,
                    name,
                    classmethod(func.validate(getattr(__class, name).__func__)),
                )

            elif isinstance(value, property) and value.fset is not None:
                # it's a property defined with a `property` tag and it has
                # a setter method linked
                setattr(
                    __class,
                    name,
                    property(
                        fget=value.fget,
                        fset=func.validate(value.fset),
                        fdel=value.fdel,
                        doc=value.__doc__,
                    ),
                )

        return __class


class func:
    @staticmethod
    def _map_args_to_kwargs_only(
        annotations: dict[str, Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> dict[str, tuple[Any, Any]]:
        if "return" in annotations.keys():
            annotations = deepcopy(annotations)
            del annotations["return"]

        combined_kwargs = {}

        for i, (key, _type) in enumerate(annotations.items()):
            # since the dictionaries are ordered starting from Python 3.7
            # this should first assign args to the corresponding keys then
            # proceed with kwargs
            if key in kwargs:
                combined_kwargs[key] = (_type, kwargs[key])
            elif i < len(args):
                combined_kwargs[key] = (_type, args[i])

        return combined_kwargs

    @staticmethod
    def validate(__func):
        @functools.wraps(__func)
        def wrapper(*args, **kwargs):
            sig = Signature.from_callable(__func)
            arguments = sig.bind(*args, **kwargs).arguments
            for key, param in sig.parameters.items():
                if (
                    key != "self"
                    and key in arguments.keys()
                    and param.annotation != Parameter.empty
                ):
                    if param.kind == Parameter.VAR_POSITIONAL:
                        # *args
                        _type = tuple[param.annotation]
                    elif param.kind == Parameter.VAR_KEYWORD:
                        # **kwargs
                        _type = dict[str, param.annotation]
                    else:
                        _type = param.annotation

                    if not isvalid(arguments[key], _type):
                        raise TypeError(
                            f"Attribute `{key}` is not valid. Expected `{_type}`, "
                            f"got `{describe_type(arguments[key]).raw}`"
                        )

            return __func(*args, **kwargs)

        return wrapper
