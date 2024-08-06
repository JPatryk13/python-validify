from types import GenericAlias, NoneType, UnionType
from typing import Any, TypeAlias, TypeGuard, get_origin, get_args


SUPPORTED_BASE_TYPES = [
    str,
    int,
    float,
    complex,
    range,
    list,
    tuple,
    dict,
    set,
    frozenset,
    bool,
    bytes,
    bytearray,
    memoryview,
    NoneType,  # type(NoneType) = type
    None,  # type(None) = NoneType
]
SUBSCRIPTABLE_BASE_TYPE = [
    list,
    tuple,
    dict,
    set,
    frozenset,
]

SupportedBaseType: TypeAlias = type | NoneType
"""Anything described by `SUPPORTED_BASE_TYPES`."""
SubscriptableBaseType: TypeAlias = list | tuple | dict | set | frozenset
"""Antything described by `SUBSCRIPTABLE_BASE_TYPE` - subset of
`SUPPORTED_BASE_TYPES`."""
NonUnionGeneric: TypeAlias = GenericAlias
"""Generics that include only memebers of the `SUPPORTED_BASE_TYPES` list.
Any unions (inc. hidden within generics) are not part of `NoUnionSupportedGeneric`.
```
tuple[str, list[int]]  # OK
tuple[str, str | int]  # Not OK! 
```
"""
SingleTypeInfo: TypeAlias = SupportedBaseType | NonUnionGeneric
"""Anything described by `SUPPORTED_BASE_TYPES` and generics that include only
memebers of the list. Any unions (inc. hidden within generics) are not part
of `SingleTypeInfo`.
"""
WithUnion: TypeAlias = GenericAlias | UnionType
"""
`UnionType` or `GenericAlias` that has a union nested within itself. It must only
include `SupportedBaseType` type elements. 
```
tuple[str, list[int]]  # Not OK!
tuple[str, str | int]  # OK
str | int  # OK
```
"""
TypeInfo: TypeAlias = (
    SingleTypeInfo | WithUnion | tuple[SingleTypeInfo | WithUnion, ...]
)


def is_supported_base_type(__val: Any) -> TypeGuard[SupportedBaseType]:
    """Validate if the given value is `SupportedBaseType`. I.e. checks
    if it is in the `SUPPORTED_BASE_TYPES` list.
    """
    return __val in SUPPORTED_BASE_TYPES


def is_subscriptable_base_type(__val: Any) -> TypeGuard[SubscriptableBaseType]:
    """Validate if the given value is `SubscriptableBaseType`. I.e. checks
    if it is in the `SUBSCRIPTABLE_BASE_TYPE` list.
    """
    return __val in SUBSCRIPTABLE_BASE_TYPE


def is_non_union_generic(__val: Any) -> TypeGuard[NonUnionGeneric]:
    """Validate if the given value is `NonUnionGeneric`. I.e. check if
    it is `GenericAlias` not containing unions within itself.
    """
    if isinstance(__val, GenericAlias):
        _valid_origin = get_origin(__val) in SUPPORTED_BASE_TYPES
        _valid_args = all(
            is_non_union_generic(v)
            or (v == ... and get_origin(__val) == tuple)
            or is_supported_base_type(v)
            for v in get_args(__val)
        )
        return _valid_origin and _valid_args

    return False


def is_single_type_info(__val: Any) -> TypeGuard[SingleTypeInfo]:
    """Validate if the given value is `SingleTypeInfo`. See `is_supported_base_type`
    and `is_non_union_generic` for more info.
    """
    return is_supported_base_type(__val) or is_non_union_generic(__val)


def is_with_union(__val: Any) -> TypeGuard[WithUnion]:
    """Validate if the given value is `WithUnion` type. I.e. Is it a union
    type of supported types or generic aliases or a generic alias that has
    a union somewhere within itself.
    """
    if isinstance(__val, UnionType):
        return all(
            is_single_type_info(arg) or is_with_union(arg) for arg in get_args(__val)
        )
    elif isinstance(__val, GenericAlias):
        return is_supported_base_type(get_origin(__val)) and any(
            is_with_union(arg) for arg in get_args(__val)
        )
    else:
        return False


def is_union(__val: Any) -> TypeGuard[UnionType]:
    return get_origin(__val) == UnionType


def is_type_info(__val: Any) -> TypeGuard[TypeInfo]:
    """Validate if the given value is `TypeInfo` - type/union/generic
    made of types specified in `SUPPORTED_BASE_TYPES`.
    """
    if isinstance(__val, tuple):
        return all(is_single_type_info(v) or is_with_union(v) for v in __val)
    else:
        return is_single_type_info(__val) or is_with_union(__val)
