from pprint import pformat
from types import NoneType
import unittest
from parameterized import parameterized
from pyparsing import Any

from src.validator import describe_type, is_valid
from src.descriptor import Descriptor
from src.type_hints import SupportedBaseType, TypeInfo


class TestValidator(unittest.TestCase):
    @parameterized.expand(
        [
            ("69", str),
            (69, int),
            (6.9, float),
            (69j, complex),
            ([6, 9], list),
            ((6, 9), tuple),
            (range(69), range),
            ({"6": 9}, dict),
            ({6, 9}, set),
            (frozenset([6, 9]), frozenset),
            (6 == 9, bool),
            (b"69", bytes),
            (bytearray(69), bytearray),
            (memoryview(b"69"), memoryview),
            (None, None),
        ]
    )
    def test_describe_type_base_type(self, _val: Any, _base: SupportedBaseType) -> None:
        """Does the function identify the base type correctly?"""
        self.assertEqual(describe_type(_val).base, _base)

    @parameterized.expand(
        [
            ([6, 9], list[int]),
            ((6,), tuple[int]),
            (("6", 9), tuple[str, int]),
            (("6", 9, 0), tuple[str, int, int]),
            ({"6": 9}, dict[str, int]),
            ({6, 9}, set[int]),
            (frozenset([6, 9]), frozenset[int]),
        ]
    )
    def test_describe_type_args_for_NonUnionGeneric_without_nesting(
        self, _val: Any, _type: type
    ) -> None:
        """Does the function identify args of simple generics (w/o nested unions) correctly?"""
        self.assertEqual(Descriptor(_type).args, describe_type(_val).args)

    @parameterized.expand(
        [
            (
                [[6, 9], [4, 2, 0]],
                Descriptor(
                    list[list[int]],
                ),
            ),
            (
                [(6, 9), (4, 4)],
                Descriptor(
                    list[tuple[int, int]],
                ),
            ),
            (
                ([6, 9],),
                Descriptor(
                    tuple[list[int]],
                ),
            ),
            (
                ([6, 9], ["6", "9"]),
                Descriptor(
                    tuple[list[int], list[str]],
                ),
            ),
            (
                ([6, 9], ("6", 9)),
                Descriptor(
                    tuple[list[int], tuple[str, int]],
                ),
            ),
            (
                {"6": (1.2, "1.2"), "9": (1.1, "1.1")},
                Descriptor(
                    dict[str, tuple[float, str]],
                ),
            ),
            (
                {(6, 9), (4, 4)},
                Descriptor(
                    set[tuple[int, int]],
                ),
            ),
            (
                frozenset([(6, b"9"), (4, b"4")]),
                Descriptor(
                    frozenset[tuple[int, bytes]],
                ),
            ),
        ]
    )
    def test_describe_type_args_for_NonUnionGeneric_with_single_level_nesting(
        self, _val: Any, _td: Descriptor
    ) -> None:
        """Does the function identify args of nested generics (w/o nested unions) correctly?"""
        self.assertEqual(_td.args, describe_type(_val).args)

    @parameterized.expand(
        [
            (
                [[[6, 9]], [[4, 2, 0]]],
                Descriptor(
                    list[list[list[int]]],
                ),
            ),
            (
                [[(6, 9), (4, 4)], [(0, 1)]],
                Descriptor(
                    list[list[tuple[int, int]]],
                ),
            ),
            (
                [([6, 9], ["6", "9"]), ([4, 4], ["4", "4"])],
                Descriptor(
                    list[tuple[list[int], list[str]]],
                ),
            ),
            (
                {"6": (1.2, ["foo", "bar", "baz"]), "9": (1.1, ["xyz", "abc"])},
                Descriptor(
                    dict[str, tuple[float, list[str]]],
                ),
            ),
            (
                {((6, 9),), ((4, 4),)},
                Descriptor(
                    set[tuple[tuple[int, int]]],
                ),
            ),
            (
                frozenset([(6, b"9"), (4, b"4")]),
                Descriptor(
                    frozenset[tuple[int, bytes]],
                ),
            ),
        ]
    )
    def test_describe_type_args_for_NonUnionGeneric_with_two_level_nesting(
        self, _val: Any, _td: Descriptor
    ) -> None:
        """Does the function identify args of nested generics (w/o nested unions) correctly?"""
        self.assertEqual(_td.args, describe_type(_val).args)

    @parameterized.expand(
        [
            # no nesting
            ([6, "9"], Descriptor(list[int | str])),
            ({"6": 9.0, "9": 42}, Descriptor(dict[str, float | int])),
            ({6, 9, "x"}, Descriptor(set[int | str])),
            (frozenset([6, 9.9]), Descriptor(frozenset[int | float])),
            # with nesting
            (
                [(6, 9), (6, "9")],
                Descriptor(list[tuple[int, int] | tuple[int, str]]),
            ),  # list[tuple[int, int | str]] is also valid
            (
                {"6": 9.0, "9": [4, (2,), (0, 0, "0")]},
                Descriptor(
                    dict[str, float | list[int | tuple[int] | tuple[int, int, str]]]
                ),
            ),
        ]
    )
    def test_describe_type_args_for_GenericAlias_WithUnion(
        self, _val: Any, _td: Descriptor
    ) -> None:
        """Does it manage to describe args for `WithUnion` type?"""
        self.assertEqual(_td.args, describe_type(_val).args)

    def test_describe_type_UnionType(self) -> None:
        """A single value cannot be a union itself, therefore I don't see situation in which
        the `describe_type` would return any `UnionType` type. This test is a placeholder
        and a reminder of the above.
        """

    def test_describe_type_max_depth(self) -> None:
        def get_type_description(max_depth: int) -> tuple[list, Descriptor]:
            if max_depth > 1:
                _val, _td = get_type_description(max_depth - 1)
                return [_val], Descriptor(base=list, args=(_td,))
            else:
                return [], Descriptor(list)

        # Two tests with manually generated values for sanity
        self.assertEqual(Descriptor(list[list[list]]), describe_type([[[]]]))  # 3
        self.assertEqual(
            Descriptor(list[list[list[list[list[list]]]]]),
            describe_type([[[[[[]]]]]]),
        )  # 6
        val, td = get_type_description(20)
        self.assertEqual(td, describe_type(val))

    @parameterized.expand(
        [
            ("base type 1", "69", str),
            ("base type 2", 69, int),
            ("union of base types 1", "69", str | bytes),
            ("union of base types 2", b"69", str | bytes),
            ("base type 3", 6.9, float),
            ("base type 4", 69j, complex),
            ("subscribed list", [6, 9], list[int]),
            ("not subscribed list", [6, 9], list),
            ("subscribed tuple", (6, 9), tuple[int, int]),
            ("base type 5", range(69), range),
            ("subscribed dict", {"6": 9}, dict[str, int]),
            ("subscribed set", {6, 9}, set[int]),
            ("subscribed frozenset", frozenset([6, 9]), frozenset[int]),
            ("base type 6", 6 == 9, bool),
            ("base type 7", b"69", bytes),
            ("base type 8", bytearray(69), bytearray),
            ("base type 9", memoryview(b"69"), memoryview),
            ("none", None, NoneType),
            (
                "tuple with two different lists",
                ([6, 9], ["6", "9"]),
                tuple[list[int], list[str]],
            ),
            (
                "tuple with a list and tuple",
                ([6, 9], ("6", 9)),
                tuple[list[int], tuple[str, int]],
            ),
            (
                "dict with tuple",
                {"6": (1.2, "1.2"), "9": (1.1, "1.1")},
                dict[str, tuple[float, str]],
            ),
            (
                "list with two different tuples",
                [(6, 9), (6, "9")],
                list[tuple[int, int] | tuple[int, str]],
            ),
            (
                "complex type 1",
                {"6": 9.0, "9": [4, (2,), (0, 0, "0")]},
                dict[str, float | list[int | tuple[int] | tuple[int, int, str]]],
            ),
            (
                "undefined length tuple 1",
                (1,),
                tuple[int, ...],
            ),
            (
                "undefined length tuple 2",
                (1, 1),
                tuple[int, ...],
            ),
            (
                "undefined length tuple 3",
                (1, 1, 1),
                tuple[int, ...],
            ),
            (
                "undefined length tuple 4",
                (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
                tuple[int, ...],
            ),
            (
                "undefined length tuple 5",
                ("1", 1, 1.0),
                tuple[str | int | float, ...],
            ),
            (
                "undefined length tuple 6",
                ("1", 1, 1.0, 1, "1", 1, "1", "1"),
                tuple[str | int | float, ...],
            ),
            (
                "dict with a simple union",
                {"a": 1, "b": 1.0},
                dict[str, int | float],
            ),
            (
                "complex type 2",
                [1, ({"a": 1.0, "b": 1.0},), 1, 1, ({"c": 1.0},)],
                list[int | tuple[dict[str, float]]],
            ),
            (
                "complex type 3",
                ("1", [1]),
                tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]],
            ),
            (
                "complex type 4",
                ("1", ("1", 1)),
                tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]],
            ),
            (
                "complex type 5",
                ("1", ("1", ("1", 1))),
                tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]],
            ),
            (
                "complex type 6",
                ("1", ("1", ("1", ("1",)))),
                tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]],
            ),
            (
                "complex type 7",
                ("1", ("1", ("1", (1.0,)))),
                tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]],
            ),
            (
                "complex type 8",
                {"a": 1, "b": 1.0},
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
            (
                "complex type 9",
                [{"a": 1, "b": 1}, {"c": 1, "d": 1}],
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
            (
                "complex type 10",
                [{"a": (1, [1], 1.0), "b": (1, [1], 1.0)}],
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
            (  # BUG: no union propagation when calculating combinations
                "complex type 11",
                [{"a": (1, [1], ("1.0", "1.0")), "b": (1, [1], ("1.0",))}],
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
            (  # BUG: no union propagation when calculating combinations
                "complex type 12",
                [{"a": (1, [1], (["1.0"], ["1.0"])), "b": (1, [1], (["1.0"],))}],
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
            (
                "complex type 13",
                [{"a": 1, "b": (1, [1], 1.0)}],
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
            (
                "complex type 14",
                [{"a": 1, "b": (1, [1], ("1.0", ["1.0"], ["1.0"]))}],
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
            ),
        ]
    )
    def test_is_valid_positive_cases(self, _: str, val: Any, _type: TypeInfo) -> None:
        self.assertTrue(
            is_valid(val, _type),
            pformat({"val": val, "type": _type, "describe_type": describe_type(val)}),
        )

    @parameterized.expand(
        [
            ("69", int),
            (69, str),
            (6.9, int),
            (69j, float),
            ([6, 9], tuple[int, int]),
            ((6, 9), list[int]),
            (range(69), tuple),
            ({"6": 9}, dict[str, float]),
            ({6, 9}, set[str]),
            (frozenset([6, 9]), frozenset[float]),
            (6 == 9, int),
            (b"69", str),
            (bytearray(69), bytes),
            (memoryview(b"69"), bytes),
            (None, str),
            (([6, 9], ["6", "9"]), tuple[list[str], list[str]]),
            (([6, 9], ("6", 9)), tuple[list[int], tuple[int, int]]),
            ({"6": (1.2, "1.2"), "9": (1.1, "1.1")}, dict[str, tuple[int, str]]),
            ([(6, 9), (6, "9")], list[tuple[int, int]]),
            (
                {"6": 9.0, "9": [4, (2,), (0, 0, "0")]},
                dict[str, list[int | tuple[int] | tuple[int, int, str]]],
            ),
        ]
    )
    def test_is_valid_negative_cases(self, val: Any, _type: TypeInfo) -> None:
        self.assertFalse(is_valid(val, _type), {"val": val, "type": _type})

    @parameterized.expand(
        [
            (([6, 9], ["6", "9"]), tuple[list[int], list[str]]),
            (([6, 9], ("6", 9)), tuple[list[int], tuple[str, int]]),
            ({"6": (1.2, "1.2"), "9": (1.1, "1.1")}, dict[str, tuple[float, str]]),
            ([(6, 9), (6, "9")], list[tuple[int, int] | tuple[int, str]]),
            (
                {"6": 9.0, "9": [4, (2,), (0, 0, "0")]},
                dict[str, float | list[int | tuple[int] | tuple[int, int, str]]],
            ),
        ]
    )
    def test_is_valid_close_match_and_complex_types(
        self, val: Any, _type: TypeInfo
    ) -> None:
        self.assertTrue(is_valid(val, _type), {"val": val, "type": _type})
