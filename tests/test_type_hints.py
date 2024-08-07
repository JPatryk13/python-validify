from types import NoneType, FunctionType
from typing import Sequence, Callable, Any, Literal
import random
import unittest
from parameterized import parameterized
from typing import Mapping
from src.pyvalidify.type_hints import (
    SUPPORTED_BASE_TYPES,
    is_single_type_info,
    is_type_info,
    is_supported_base_type,
    is_non_union_generic,
    is_with_union,
)

supported_generics_sample = [
    # subscripted generics - with non-subscriptables
    (list[int],),
    (tuple[str],),
    (tuple[str, int, float],),
    (tuple[str, ...],),
    (dict[str, float],),
    (set[str],),
    (frozenset[str],),
    # subscripted generics - with unsub. subscriptables
    (list[tuple],),
    (tuple[list, ...],),
    (dict[str, set],),
    (set[dict],),
    (frozenset[frozenset],),
    # subscripted generics - nested
    (list[tuple[str, ...]],),
    (tuple[list[int], ...],),
    (dict[str, set[bool]],),
    (set[dict[str, dict[str, int]]],),
    (frozenset[frozenset[list[float]]],),
]
supported_unions_sample = [
    (str | set,),
    (int | frozenset,),
    (float | bool,),
    (complex | bytes,),
    (list | bytearray,),
    (tuple | memoryview,),
    (range | NoneType,),
    (dict | None,),
]


class TestIsSupportedBaseType(unittest.TestCase):
    @parameterized.expand([(t,) for t in SUPPORTED_BASE_TYPES])
    def test_with_supported_base_types_returns_true(self, _type: Any) -> None:
        self.assertTrue(is_supported_base_type(_type))

    @parameterized.expand(
        [
            # random sample
            (Any,),
            (Literal,),
            (FunctionType,),
            (Sequence,),
            # nested union
            (list[str | int],),
            # generics with nested unsuported types or union
            (list[dict[str, Any]],),
            (list[Sequence],),
            # subscripted generics
            (Callable[..., int],),
            (Literal["foo", "bar"],),
        ]
        + random.sample(supported_generics_sample, 5)
        + random.sample(supported_unions_sample, 3)
    )
    def test_returns_false_for_anything_thats_not_in_SUPPORTED_BASE_TYPES(
        self, _type: Any
    ) -> None:
        self.assertFalse(is_supported_base_type(_type))


class TestIsNonUnionGeneric(unittest.TestCase):
    @parameterized.expand(supported_generics_sample)
    def test_returns_true_for_supported_generics(self, _type: Any) -> None:
        self.assertTrue(is_non_union_generic(_type))

    @parameterized.expand(
        [(t,) for t in SUPPORTED_BASE_TYPES] + supported_unions_sample
    )
    def test_returns_false_for_non_generics(self, _type: Any) -> None:
        self.assertFalse(is_non_union_generic(_type))

    @parameterized.expand(
        [
            (list[str | int],),
            (list[list[list[list[str | int]]]],),
        ]
    )
    def test_returns_false_for_generics_with_nested_unions(self, _type: Any) -> None:
        self.assertFalse(is_non_union_generic(_type))


class TestIsSingleTypeInfo(unittest.TestCase):

    @parameterized.expand([(t,) for t in SUPPORTED_BASE_TYPES])
    def test_with_supported_base_types_returns_true(self, _type: Any) -> None:
        self.assertTrue(is_single_type_info(_type))

    @parameterized.expand(
        [
            # random sample
            (Any,),
            (Literal,),
            (FunctionType,),
            (Sequence,),
        ]
    )
    def test_with_unsupported_unsubscribed_types_returns_false(
        self, _type: Any
    ) -> None:
        self.assertFalse(is_single_type_info(_type))

    @parameterized.expand(supported_generics_sample)
    def test_with_supported_generics_returns_true(self, _type: Any) -> None:
        self.assertTrue(is_single_type_info(_type))

    @parameterized.expand(
        [
            # nested union
            (list[str | int],),
            # generics with nested unsuported types or union
            (list[dict[str, Any]],),
            (list[Sequence],),
            # subscripted generics
            (Callable[..., int],),
            (Literal["foo", "bar"],),
        ]
    )
    def test_with_unsupported_generics_returns_false(self, _type: Any) -> None:
        self.assertFalse(is_single_type_info(_type))

    @parameterized.expand(supported_unions_sample)
    def test_wtih_unions_returns_false(self, _type: Any) -> None:
        self.assertFalse(is_single_type_info(_type))


class TestIsWithUnion(unittest.TestCase):
    @parameterized.expand(supported_unions_sample)
    def test_returns_true_for_union_type_of_supported_base_types(
        self, _type: Any
    ) -> None:
        self.assertTrue(is_with_union(_type))

    @parameterized.expand(
        [
            (list[str | int],),
            (list[list[list[list[str | int]]]],),
            (tuple[str, str | int],),
        ]
    )
    def test_returns_true_for_generics_that_have_nested_unions(
        self, _type: Any
    ) -> None:
        self.assertTrue(is_with_union(_type))

    @parameterized.expand([(t,) for t in SUPPORTED_BASE_TYPES])
    def test_returns_false_for_non_union_and_non_generic_types(
        self, _type: Any
    ) -> None:
        self.assertFalse(is_with_union(_type))

    @parameterized.expand(
        [
            (str | Callable,),
            (int | list[tuple[str, Any]],),
        ]
    )
    def test_returns_false_for_union_types_that_have_not_supported_types(
        self, _type: Any
    ) -> None:
        self.assertFalse(is_with_union(_type))

    @parameterized.expand(
        [
            (list[dict[str, Any]],),
            (list[Sequence],),
        ]
    )
    def test_returns_false_for_generics_that_have_not_supported_types(
        self, _type: Any
    ) -> None:
        self.assertFalse(is_with_union(_type))


class TestIsTypeInfo(unittest.TestCase):
    @parameterized.expand(
        [(t,) for t in SUPPORTED_BASE_TYPES] + supported_generics_sample
    )
    def test_returns_true_when_is_single_type_info_returns_true(
        self, _type: Any
    ) -> None:
        self.assertTrue(is_type_info(_type))

    @parameterized.expand(
        supported_unions_sample
        + [
            # tuples - unsubscribed types
            (
                (
                    str,
                    set,
                ),
            ),
            (
                (
                    int,
                    frozenset,
                ),
            ),
            (
                (
                    float,
                    bool,
                ),
            ),
            (
                (
                    complex,
                    bytes,
                ),
            ),
            (
                (
                    list,
                    bytearray,
                ),
            ),
            (
                (
                    tuple,
                    memoryview,
                ),
            ),
            (
                (
                    range,
                    NoneType,
                ),
            ),
            (
                (
                    dict,
                    None,
                ),
            ),
            # tuples - subscribed types
            ((list[int], set[dict]),),
            ((tuple[str, int, float], tuple[list[int], ...]),),
            ((frozenset[str], dict[str, set[bool]]),),
            # nested unions
            (list[str | int],),
            (list[list[list[list[str | int]]]],),
            (tuple[str, str | int],),
        ]
    )
    def test_returns_true_for_unions_and_tuples_of_supported_types(
        self, _type: Any | tuple
    ) -> None:
        self.assertTrue(is_type_info(_type))

    @parameterized.expand(
        [
            # unsubscribed types
            (Any,),
            (FunctionType,),
            (Sequence,),
            # generics with nested unsuported types or union
            (list[Mapping[str, Any]],),
            (list[str | Sequence],),
            # subscripted generics
            (Callable[..., int],),
            (Literal["foo", "bar"],),
            # tuples - unsubscribed types
            (
                (
                    str,
                    Any,
                ),
            ),
            ((int, frozenset, Sequence),),
            # tuples - subscribed types
            ((Sequence[int], set[dict]),),
            ((frozenset[str], dict[str, set[Any]]),),
        ]
    )
    def test_returns_false_for_unsupported_types(self, _type: Any | tuple) -> None:
        self.assertFalse(is_type_info(_type))
