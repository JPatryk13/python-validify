from pprint import pformat
from typing import Literal, cast
import unittest

from parameterized import parameterized
from src.pyvalidify.descriptor import Descriptor
from src.pyvalidify.type_hints import SingleTypeInfo, SupportedBaseType, TypeInfo, WithUnion

td_ = Descriptor


class TestDescriptor(unittest.TestCase):

    @parameterized.expand(
        [
            ("SupportedBaseType", int, int, tuple()),
            ("NonUnionGeneric", list[str], list, (Descriptor(str),)),
            (
                "WithUnion (GenericAlias)",
                tuple[str, str | int],
                tuple,
                (Descriptor(str), Descriptor(str | int)),
            ),
            (
                "WithUnion (UnionType)",
                str | list[str],
                None,
                (Descriptor(str), Descriptor(list[str])),
            ),
            (
                "union as tuple",
                (str, list[str]),
                None,
                (Descriptor(str), Descriptor(list[str])),
            ),
        ]
    )
    def test_init_from_type_info(
        self,
        _: str,
        _input: TypeInfo,
        base: SupportedBaseType | None,
        args: tuple[Descriptor, ...],
    ) -> None:
        """Initializing Descriptor. Passing positional argument
        to the init.
        """
        td = Descriptor(_input)
        self.assertEqual(base, td.base)
        self.assertEqual(args, td.args)

    @parameterized.expand(
        [
            ("SupportedBaseType", {"base": int}, int, tuple()),
            (
                "NonUnionGeneric",
                {"base": list, "args": (str,)},
                list,
                (Descriptor(str),),
            ),
            (
                "NonUnionGeneric - args as Descriptor instances",
                {"base": list, "args": (Descriptor(str),)},
                list,
                (Descriptor(str),),
            ),
            (
                "WithUnion (GenericAlias)",
                {"base": tuple, "args": (str, str | int)},
                tuple,
                (Descriptor(str), Descriptor(str | int)),
            ),
            (
                "WithUnion (GenericAlias) - args as Descriptor instances",
                {
                    "base": tuple,
                    "args": (Descriptor(str), Descriptor(str | int)),
                },
                tuple,
                (Descriptor(str), Descriptor(str | int)),
            ),
            (
                "WithUnion (GenericAlias) - mixed args",
                {"base": tuple, "args": (Descriptor(str), str | int)},
                tuple,
                (Descriptor(str), Descriptor(str | int)),
            ),
            (
                "WithUnion (UnionType)",
                {"args": (str, list[str])},
                None,
                (Descriptor(str), Descriptor(list[str])),
            ),
        ]
    )
    def test_init_from_kwargs(
        self,
        _: str,
        _input: dict,
        base: SupportedBaseType | None,
        args: tuple[Descriptor, ...],
    ) -> None:
        """Initializing Descriptor with `base` and/or `args` keyword arguments."""
        td = Descriptor(**_input)
        self.assertEqual(base, td.base)
        if td.base == None:
            # order of arguments does not matter
            self.assertEqual(len(args), len(td.args))
            self.assertEqual(set(args), set(td.args))
        else:
            self.assertEqual(args, td.args)

    def test_init_no_arguments_given(self) -> None:
        """Descriptor initializer raises error when given incompatible input
        - case #1: no arguments given."""
        self.assertEqual(None, Descriptor().raw)
        self.assertEqual("Descriptor( None )", str(Descriptor()))

    @parameterized.expand(
        [
            # SupportedBaseType
            (str, {"base": str}, str, {"base": str}, True),
            (str, {"base": str}, int, {"base": int}, False),
            (list, {"base": list}, list, {"base": list}, True),
            # NonUnionGeneric
            (
                list[str],
                {"base": list, "args": (str,)},
                list[str],
                {"base": list, "args": (str,)},
                True,
            ),
            (
                list[str],
                {"base": list, "args": (str,)},
                list[list[str]],
                {"base": list, "args": (list[str],)},
                False,
            ),
            (
                list[str],
                {"base": list, "args": (str,)},
                list[int],
                {"base": list, "args": (int,)},
                False,
            ),
            (
                list[str],
                {"base": list, "args": (str,)},
                tuple[str],
                {"base": tuple, "args": (str,)},
                False,
            ),
            (list[str], {"base": list, "args": (str,)}, list, {"base": list}, False),
            (
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                True,
            ),
            (
                tuple[int, str],
                {"base": tuple, "args": (int, str)},
                tuple[str, int],
                {"base": tuple, "args": (str, int)},
                False,
            ),
            (
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                tuple[str],
                {"base": tuple, "args": (str,)},
                False,
            ),
            (
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                tuple[str, ...],
                {"base": tuple, "args": (str, ...)},
                False,
            ),
            (
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                tuple[str, str | int],
                {"base": tuple, "args": (str, str | int)},
                False,
            ),
            (
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                tuple[str, str, str],
                {"base": tuple, "args": (str, str, str)},
                False,
            ),
            (
                tuple[str, str],
                {"base": tuple, "args": (str, str)},
                tuple[str, str, int],
                {"base": tuple, "args": (str, str, int)},
                False,
            ),
            (
                dict[str, str],
                {"base": dict, "args": (str, str)},
                dict[str, str],
                {"base": dict, "args": (str, str)},
                True,
            ),
            (
                dict[str, str],
                {"base": dict, "args": (str, str)},
                dict[str, str | int],
                {"base": dict, "args": (str, str | int)},
                False,
            ),
            (
                dict[str, str],
                {"base": dict, "args": (str, str)},
                dict[str, int],
                {"base": dict, "args": (str, int)},
                False,
            ),
            (
                dict[str, str],
                {"base": dict, "args": (str, str)},
                dict[int, str],
                {"base": dict, "args": (int, str)},
                False,
            ),
            # WithUnion - UnionType
            (str | int, {"args": (str, int)}, str | int, {"args": (str, int)}, True),
            (str | int, {"args": (str, int)}, (str, int), {"args": (str, int)}, True),
            (str | int, {"args": (str, int)}, int | str, {"args": (int, str)}, True),
            (
                str | int | float,
                {"args": (str, int, float)},
                int | float | str,
                {"args": (int, float, str)},
                True,
            ),
            (
                str | int,
                {"args": (str, int)},
                str | float,
                {"args": (str, float)},
                False,
            ),
            (
                str | int | float,
                {"args": (str, int, float)},
                str | int,
                {"args": (str, int)},
                False,
            ),
            # WithUnion - GenericAlias
            (
                tuple[str, int | float],
                {"base": tuple, "args": (str, int | float)},
                tuple[str, int | float],
                {"base": tuple, "args": (str, int | float)},
                True,
            ),
            (
                tuple[str, list[int | float]],
                {"base": tuple, "args": (str, list[int | float])},
                tuple[str, list[int | float]],
                {"base": tuple, "args": (str, list[int | float])},
                True,
            ),
            (
                list[str | int],
                {"base": list, "args": (str | int,)},
                list[str | int],
                {"base": list, "args": (str | int,)},
                True,
            ),
            (
                list[str | int | float],
                {"base": list, "args": (str | int | float,)},
                list[int | float | str],
                {"base": list, "args": (int | float | str,)},
                True,
            ),
            (
                tuple[str, list[int | float]],
                {"base": tuple, "args": (str, list[int | float])},
                tuple[str, list[int]],
                {"base": tuple, "args": (str, list[int])},
                False,
            ),
            (
                list[str | int],
                {"base": list, "args": (str | int,)},
                list[str] | list[int],
                {"args": (list[str], list[int])},
                False,
            ),
            (
                tuple[str | int],
                {"base": tuple, "args": (str | int,)},
                tuple[str] | tuple[int],
                {"args": (tuple[str], tuple[int])},
                True,
            ),
            (
                tuple[str | int, ...],
                {"base": tuple, "args": (str | int, ...)},
                tuple[str, ...] | tuple[int, ...],
                {"args": (tuple[str, ...], tuple[int, ...])},
                False,
            ),
            (
                list[str | int],
                {"base": list, "args": (str | int,)},
                list[str | float],
                {"base": list, "args": (str | float,)},
                False,
            ),
            (
                list[str | int | float],
                {"base": list, "args": (str | int | float,)},
                list[str | int],
                {"base": list, "args": (str | int,)},
                False,
            ),
        ],
        name_func=lambda func, _, param: f"{func.__name__}__{parameterized.to_safe_name('__'.join([str(param.args[0]), str(param.args[2])]))}",
    )
    def test_eq(
        self,
        left_args: TypeInfo,
        left_kwargs: dict[str, TypeInfo],
        right_args: TypeInfo,
        right_kwargs: dict[str, TypeInfo],
        is_equal: bool,
    ) -> None:
        """Tests if the __eq__ is implemented correctly - we expect two instances
        with the same bases and args to be equal."""
        # symmetry
        self.assertEqual(Descriptor(left_args) == Descriptor(right_args), is_equal)
        self.assertEqual(Descriptor(right_args) == Descriptor(left_args), is_equal)
        if Descriptor(left_args) == Descriptor(**left_kwargs) and Descriptor(
            right_args
        ) == Descriptor(**right_kwargs):
            # equivalence
            self.assertEqual(
                Descriptor(**left_kwargs) == Descriptor(right_args), is_equal
            )
            self.assertEqual(
                Descriptor(**left_kwargs) == Descriptor(**right_kwargs),
                is_equal,
            )
            self.assertEqual(
                Descriptor(left_args) == Descriptor(**right_kwargs), is_equal
            )
        else:
            raise Exception("Oops! Something went wrong.")

    @parameterized.expand(
        [
            (str, {"base": str}, ["Descriptor( str )"]),
            (
                str | int,
                {"args": (str, int)},
                ["Descriptor( str | int )", "Descriptor( int | str )"],
            ),
            (
                list[str],
                {"base": list, "args": (str,)},
                ["Descriptor( list[str] )"],
            ),
            (
                tuple[str, ...],
                {"base": tuple, "args": (str, ...)},
                ["Descriptor( tuple[str, ...] )"],
            ),
            (
                list[tuple[int | None]],
                {"base": list, "args": (tuple[int | None],)},
                [
                    "Descriptor( list[tuple[int | None]] )",
                    "Descriptor( list[tuple[None | int]] )",
                ],
            ),
            (
                dict[str, float | tuple[int | tuple[int], tuple[int, int, str]]],
                {
                    "base": dict,
                    "args": (
                        str,
                        float | tuple[int | tuple[int], tuple[int, int, str]],
                    ),
                },
                [
                    "Descriptor( dict[str, float | tuple[int | tuple[int], tuple[int, int, str]]] )",
                    "Descriptor( dict[str, float | tuple[tuple[int] | int, tuple[int, int, str]]] )",
                    "Descriptor( dict[str, tuple[int | tuple[int], tuple[int, int, str]] | float] )",
                    "Descriptor( dict[str, tuple[tuple[int] | int, tuple[int, int, str]] | float] )",
                ],
            ),
        ]
    )
    def test_repr(self, _type: TypeInfo, kwargs: dict, expected: list[str]) -> None:
        """Test if the repr is not giberish."""
        self.assertIn(repr(Descriptor(_type)), expected)
        self.assertIn(repr(Descriptor(**kwargs)), expected)

    @parameterized.expand(
        [
            ({"base": str}, str),
            ({"base": list, "args": (str,)}, list[str]),
            (
                {"base": list, "args": (Descriptor(args=(str, int)),)},
                list[str | int],
            ),
            (
                {"base": tuple, "args": (str, int, int | float)},
                tuple[str, int, int | float],
            ),
            ({"base": dict, "args": (str, int | float)}, dict[str, int | float]),
            (
                {
                    "base": list,
                    "args": (Descriptor(int | tuple[dict[str, float]]),),
                },
                list[int | tuple[dict[str, float]]],
            ),
        ]
    )
    def test_raw_property(self, kwargs: dict, _type: TypeInfo) -> None:
        self.assertEqual(_type, Descriptor(_type).raw)
        self.assertEqual(_type, Descriptor(**kwargs).raw)

    def test_parent_property_linear_case(self) -> None:
        td = td_(list[list[tuple[int]]])
        # parent for list[list[tuple[int]]]
        self.assertEqual(None, td.parent)
        # parent for list[tuple[int]]
        child0 = td.args[0]
        self.assertEqual(child0.raw, list[tuple[int]])
        self.assertEqual(td_(list[list[tuple[int]]]), child0.parent)
        self.assertEqual(
            None, child0.parent.parent  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for tuple[int]
        child1 = child0.args[0]
        self.assertEqual(child1.raw, tuple[int])
        self.assertEqual(td_(list[tuple[int]]), child1.parent)
        self.assertEqual(
            td_(list[list[tuple[int]]]),
            child1.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child1.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for int
        child2 = child1.args[0]
        self.assertEqual(child2.raw, int)
        self.assertEqual(td_(tuple[int]), child2.parent)
        self.assertEqual(
            td_(list[tuple[int]]),
            child2.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(list[list[tuple[int]]]),
            child2.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child2.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )

    def test_parent_property_non_linear_case(self) -> None:
        td = td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]])
        # parent for list[int] | tuple[...]
        self.assertEqual(None, td.parent)
        # parent for list[int]
        child0a = td.args[0]
        self.assertEqual(child0a.raw, list[int])
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child0a.parent,
        )
        self.assertEqual(
            None,
            child0a.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for tuple[...]
        child0b = td.args[1]
        self.assertEqual(child0b.raw, tuple[dict[str, bytes], dict[str, list[bytes]]])
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child0b.parent,
        )
        self.assertEqual(
            None,
            child0b.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for int
        child1a = child0a.args[0]
        self.assertEqual(child1a.raw, int)
        self.assertEqual(td_(list[int]), child1a.parent)
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child1a.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child1a.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for dict[str, bytes]
        child1ba = child0b.args[0]
        self.assertEqual(child1ba.raw, dict[str, bytes])
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]), child1ba.parent
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child1ba.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child1ba.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for str
        child2ba_str = child1ba.args[0]
        self.assertEqual(child2ba_str.raw, str)
        self.assertEqual(td_(dict[str, bytes]), child2ba_str.parent)
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2ba_str.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2ba_str.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child2ba_str.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for bytes
        child2ba_bytes = child1ba.args[1]
        self.assertEqual(child2ba_bytes.raw, bytes)
        self.assertEqual(td_(dict[str, bytes]), child2ba_bytes.parent)
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2ba_bytes.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2ba_bytes.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child2ba_bytes.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for dict[str, list[bytes]]
        child1bb = child0b.args[1]
        self.assertEqual(child1bb.raw, dict[str, list[bytes]])
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]), child1bb.parent
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child1bb.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child1bb.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for str
        child2bb_str = child1bb.args[0]
        self.assertEqual(child2bb_str.raw, str)
        self.assertEqual(td_(dict[str, list[bytes]]), child2bb_str.parent)
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2bb_str.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2bb_str.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child2bb_str.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for list[bytes]
        child2bb_list = child1bb.args[1]
        self.assertEqual(child2bb_list.raw, list[bytes])
        self.assertEqual(td_(dict[str, list[bytes]]), child2bb_list.parent)
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2bb_list.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child2bb_list.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child2bb_list.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        # parent for bytes
        child3bb_bytes = child2bb_list.args[0]
        self.assertEqual(child3bb_bytes.raw, bytes)
        self.assertEqual(td_(list[bytes]), child3bb_bytes.parent)
        self.assertEqual(
            td_(dict[str, list[bytes]]),
            child3bb_bytes.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child3bb_bytes.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            td_(list[int] | tuple[dict[str, bytes], dict[str, list[bytes]]]),
            child3bb_bytes.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )
        self.assertEqual(
            None,
            child3bb_bytes.parent.parent.parent.parent.parent,  # pyright: ignore [reportOptionalMemberAccess]
        )

    @parameterized.expand(
        [
            (str, 0),
            (list[str], 1),
            (list[str | int], 1),
            (list[str] | list[int], 1),
            (list[str] | tuple[list[str]], 2),
            (tuple[str, ...], 1),
            (dict[str, int | float], 1),
            (list[int | tuple[dict[str, float]]], 3),
            (tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]], 3),
        ]
    )
    def test_depth_property(
        self, raw_type: SingleTypeInfo | WithUnion, expected_depth: int
    ) -> None:
        self.assertEqual(
            expected_depth,
            Descriptor(raw_type).depth,
        )

    @parameterized.expand(
        [
            (str, str, ()),
            (list, list, ()),
            (list[str], list, (str,)),
            (
                list[list[tuple[int, int | list[int]]]],
                list[list[tuple[int, int | list]]],
                (int,),
            ),
            (list[str] | tuple[int, list[int]], list[str] | tuple[int, list], (int,)),
            (list[str] | tuple[int, list], list | tuple, (str, int, list)),
            (tuple[str, int] | tuple[int], tuple, (str, int, int)),
            (list[str | int], list, (str | int,)),
        ]
    )
    def test__remove_inner(
        self,
        raw_type: SingleTypeInfo | WithUnion,
        raw_reduced: SingleTypeInfo | WithUnion,
        raw_remainder: tuple[SingleTypeInfo | WithUnion, ...],
    ) -> None:
        actual_reduced, actual_remainder = Descriptor(raw_type)._remove_inner()
        expected_reduced_return_val = Descriptor(raw_reduced)
        expected_remainder_return_val = tuple(Descriptor(raw) for raw in raw_remainder)
        self.assertEqual(expected_reduced_return_val, actual_reduced)
        self.assertEqual(expected_remainder_return_val, actual_remainder)

    @parameterized.expand(
        [
            (str, [str]),
            (list, [list]),
            (list[str], [list, list[str]]),
            (
                list[list[tuple[int, int | list[int]]]],
                [
                    list[list[tuple[int, int | list[int]]]],
                    list[list[tuple[int, int | list]]],
                    list[list[tuple]],
                    list[list],
                    list,
                ],
            ),
            (
                list[str] | tuple[int, list[int]],
                [
                    list[str] | tuple[int, list[int]],
                    list[str] | tuple[int, list],
                    list | tuple,
                ],
            ),
            (tuple[str, int] | tuple[int], [tuple[str, int] | tuple[int], tuple]),
            (list[str | int], [list[str | int], list]),
        ]
    )
    def test_reductions(
        self,
        raw_type: SingleTypeInfo | WithUnion,
        expected_raw: list[SingleTypeInfo | WithUnion],
    ) -> None:
        actual = Descriptor(raw_type).reductions()
        expected = [Descriptor(raw) for raw in expected_raw]
        self.assertEqual(len(expected), len(actual))
        self.assertEqual(set(expected), set(actual))

    @parameterized.expand(
        [
            (str, []),
            (list, []),
            (list[str], [((str,),)]),
            (list[tuple[int | str]], [((tuple[int | str],),)]),
            (str | int, [((str,),), ((int,),)]),
            (
                list[str | int],
                [
                    ((str,), (int,), (str, int)),
                ],
            ),
            (
                tuple[str | int],
                [
                    ((str,), (int,), (str, int)),
                ],
            ),
            (
                tuple[str, str | int],
                [
                    ((str,),),
                    ((str,), (int,), (str, int)),
                ],
            ),
            (
                tuple[str | int, ...],
                [
                    ((str,), (int,), (str, int)),
                ],
            ),
        ]
    )
    def test__group_args(
        self,
        raw_type: SingleTypeInfo | WithUnion,
        expected_raw: list[tuple[tuple[SingleTypeInfo | WithUnion, ...], ...]],
    ) -> None:
        actual = Descriptor(raw_type)._group_args()
        expected = []
        for arg_group in expected_raw:
            td_arg_group = []
            for combination in arg_group:
                td_combination = []
                for raw in combination:
                    td_combination.append(Descriptor(raw))
                td_arg_group.append(tuple(td_combination))
            expected.append(tuple(td_arg_group))

        self.assertEqual(expected, actual)

    @parameterized.expand(
        [
            (str, [str]),
            (list, [list]),
            (list[str], [list[str]]),
            (list[tuple[int | str]], [list[tuple[int | str]]]),
            (str | int, [str | int]),
            (
                list[str | int],
                [
                    list[str],
                    list[int],
                    list[str | int],
                ],
            ),
            (
                tuple[str | int],
                [
                    tuple[str],
                    tuple[int],
                ],
            ),
            (
                tuple[str, str | int],
                [
                    tuple[str, str],
                    tuple[str, int],
                ],
            ),
            (
                tuple[str | int, ...],
                [tuple[str, ...], tuple[int, ...], tuple[str | int, ...]],
            ),
        ]
    )
    def test__transformed_groups(
        self,
        raw_type: SingleTypeInfo | WithUnion,
        expected_raw: list[SingleTypeInfo | WithUnion],
    ) -> None:
        actual = Descriptor(raw_type)._transformed_groups()
        expected = [Descriptor(raw) for raw in expected_raw]
        self.assertEqual(expected, actual, {"raw_type": raw_type})

    @parameterized.expand(
        [
            (str, [str]),
            (
                list[str],
                [list[str]],
            ),
            (
                list[str | int],
                [list[str | int], list[str], list[int]],
            ),
            (
                list[str] | list[int],
                [list[str], list[int]],
            ),
            (
                list[str] | tuple[int],
                [list[str], tuple[int]],
            ),
            (
                tuple[str, ...],
                [tuple[str, ...]],
            ),
            (
                tuple[str | int | float, ...],
                [
                    tuple[str, ...],
                    tuple[int, ...],
                    tuple[float, ...],
                    tuple[str | int, ...],
                    tuple[str | float, ...],
                    tuple[int | float, ...],
                    tuple[str | int | float, ...],
                ],
            ),
            (
                dict[str, int | float],
                [dict[str, int | float], dict[str, int], dict[str, float]],
            ),
            (
                list[int | tuple[dict[str, float]]],
                [
                    list[int | tuple[dict[str, float]]],
                    list[int],
                    list[tuple[dict[str, float]]],
                ],
            ),
            # (  # BUG: no union propagation
            #     list[tuple[int | str]],
            #     [
            #         list[tuple[int]],
            #         list[tuple[str]],
            #         list[tuple[int] | tuple[str]],
            #     ],
            # ),
            # (  # BUG: no union propagation
            #     list[list[tuple[int | str]]],
            #     [
            #         list[list[tuple[int]]],
            #         list[list[tuple[str]]],
            #         list[list[tuple[int] | tuple[str]]],
            #         list[list[tuple[int]] | list[tuple[str]]],
            #     ],
            # ),
            # (  # BUG: no union propagation
            #     list[tuple[tuple[int | str]]],
            #     [
            #         list[tuple[tuple[int]]],
            #         list[tuple[tuple[str]]],
            #         list[tuple[tuple[int]] | tuple[tuple[str]]],
            #     ],
            # ),
            # (  # BUG: no union propagation
            #     list[tuple[tuple[int | str], ...]],
            #     [
            #         list[tuple[tuple[int], ...]],
            #         list[tuple[tuple[str], ...]],
            #         list[tuple[tuple[int] | tuple[str], ...]],
            #         list[tuple[tuple[int], ...] | tuple[tuple[str], ...]],
            #     ],
            # ),
            (
                tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]],
                [
                    tuple[str, list[int]],
                    tuple[str, tuple[str, int]],
                    tuple[str, tuple[str, tuple[str, int]]],
                    tuple[str, tuple[str, tuple[str, tuple]]],
                ],
            ),
            (
                dict
                | list[
                    dict[
                        str,
                        int
                        | tuple[int, list[int], float | tuple[str | list[str], ...]],
                    ]
                ],
                [
                    dict,
                    list[dict[str, int]],
                    list[dict[str, tuple[int, list[int], float]]],
                    list[dict[str, tuple[int, list[int], tuple[str | list[str], ...]]]],
                    list[dict[str, tuple[int, list[int], tuple[list[str], ...]]]],
                    list[dict[str, tuple[int, list[int], tuple[str, ...]]]],
                    list[dict[str, int | tuple[int, list[int], float]]],
                    list[
                        dict[
                            str,
                            int | tuple[int, list[int], tuple[str | list[str], ...]],
                        ]
                    ],
                    list[dict[str, int | tuple[int, list[int], tuple[list[str], ...]]]],
                    list[dict[str, int | tuple[int, list[int], tuple[str, ...]]]],
                ],
            ),
        ]
    )
    def test_combinations(
        self,
        raw_type: SingleTypeInfo | WithUnion,
        expected_raw_combinations: list[SingleTypeInfo | WithUnion],
    ) -> None:
        actual = Descriptor(raw_type).combinations()
        expected = [Descriptor(raw) for raw in expected_raw_combinations]
        _msg = pformat({"expected": expected, "actual": actual}, indent=4)
        self.assertEqual(len(expected), len(actual), _msg)
        self.assertEqual(set(expected), set(actual), _msg)

    @parameterized.expand(
        [
            (str, 1),
            (list[str], "undefined"),
            (list[str | int], "undefined"),
            (list[str] | list[int], 1),
            (tuple[str, ...], "undefined"),
            (tuple[str | int | float, ...], "undefined"),
            (dict[str, int | float], "undefined"),
            (tuple[str, list[int]], 2),
        ]
    )
    def test_length_property(
        self, raw_type: SingleTypeInfo | WithUnion, expected: int | str
    ) -> None:
        actual = Descriptor(raw_type).length
        self.assertEqual(expected, actual)

    @parameterized.expand(
        [
            ({"base": str}, 1, 0),
            ({"base": list, "args": (str,)}, "undefined", 1),
            ({"base": list, "args": (str | int,)}, "undefined", 2),
            ({"args": (list[str], list[int])}, 1, 2),
            ({"base": tuple, "args": (str, ...)}, "undefined", 1),
            ({"base": tuple, "args": (str | int | float, ...)}, "undefined", 1),
            ({"base": dict, "args": (str, int | float)}, "undefined", 2),
            ({"base": tuple, "args": (str, list[int])}, 2, "undefined"),
        ]
    )
    def test_length_manual_input_validation(
        self,
        _input: dict,
        valid: int | Literal["undefined"],
        invalid: int | Literal["undefined"],
    ) -> None:
        # positive case
        try:
            Descriptor(**_input, _length=valid)
        except ValueError as e:
            self.fail(
                f"Failed for {Descriptor(**_input)} -- given length: {valid} -- error: {e}"
            )

        # negative case
        with self.assertRaises(ValueError):
            Descriptor(**_input, _length=invalid)

    def test_length_property_becomes_undefined_after_no_args(self) -> None:
        td = Descriptor(tuple[int, str, str])
        self.assertEqual(td.length, 3)
        self.assertEqual(cast(Descriptor, td.no_args).length, "undefined")

    def test_reductions_preserve_length_property(self) -> None:
        reds = Descriptor(
            tuple[str, list[int] | tuple[str, int | tuple[str, int | tuple]]]
        ).reductions()

        red_0_index = reds.index(
            Descriptor(tuple[str, list[int] | tuple[str, int | tuple]])
        )
        self.assertEqual(reds[red_0_index].length, 2)
        sub_0_index = (
            reds[red_0_index].args[1].args.index(Descriptor(tuple[str, int | tuple]))
        )
        self.assertEqual(reds[red_0_index].args[1].args[sub_0_index].length, 2)
        sub_1_index = (
            reds[red_0_index]
            .args[1]
            .args[sub_0_index]
            .args[1]
            .args.index(Descriptor(tuple))
        )
        self.assertEqual(
            reds[red_0_index]
            .args[1]
            .args[sub_0_index]
            .args[1]
            .args[sub_1_index]
            .length,
            "undefined",
        )

        red_1_index = reds.index(Descriptor(tuple[str, list | tuple]))
        self.assertEqual(reds[red_1_index].length, 2)
        sub_2_index = reds[red_1_index].args[1].args.index(Descriptor(tuple))
        self.assertEqual(
            reds[red_1_index].args[1].args[sub_2_index].length, "undefined"
        )

        red_2_index = reds.index(Descriptor(tuple))
        self.assertEqual(reds[red_2_index].length, "undefined")

    def test_combinations_output_inherits_correct_length(self) -> None:
        combinations = Descriptor(
            list[int | str] | tuple[int | str, int]
        ).combinations()

        cmb_0_index = combinations.index(Descriptor(list[int | str]))
        self.assertEqual(combinations[cmb_0_index].length, "undefined")

        cmb_1_index = combinations.index(Descriptor(list[int]))
        self.assertEqual(combinations[cmb_1_index].length, "undefined")

        cmb_2_index = combinations.index(Descriptor(list[str]))
        self.assertEqual(combinations[cmb_2_index].length, "undefined")

        cmb_3_index = combinations.index(Descriptor(tuple[int, int]))
        self.assertEqual(combinations[cmb_3_index].length, 2)

        cmb_4_index = combinations.index(Descriptor(tuple[str, int]))
        self.assertEqual(combinations[cmb_4_index].length, 2)

    @parameterized.expand(
        [
            (Descriptor(tuple[int, ...]), Descriptor(tuple[int, ...])),
            (Descriptor(tuple[int]), Descriptor(tuple[int, ...])),
            (Descriptor(tuple[int, int]), Descriptor(tuple[int, ...])),
            (Descriptor(tuple[int, str]), Descriptor(tuple[int | str, ...])),
            (Descriptor(tuple[int, int, int]), Descriptor(tuple[int, ...])),
            (
                Descriptor(tuple[int, int, int, int]),
                Descriptor(tuple[int, ...]),
            ),
            (
                Descriptor(tuple[int, int, int, int]),
                Descriptor(tuple[int, ...]),
            ),
            (
                Descriptor(tuple[tuple[str, str], int]),
                Descriptor(tuple[tuple[str, str] | int, ...]),
            ),
            (
                Descriptor(list[tuple[str, str]]),
                Descriptor(list[tuple[str, str]]),
            ),
            (Descriptor(list[str]), Descriptor(list[str])),
            (Descriptor(str), Descriptor(str)),
            (Descriptor(tuple), Descriptor(tuple)),
        ]
    )
    def test__set_tuple_undefined(
        self, given: Descriptor, expected: Descriptor
    ) -> None:
        self.assertEqual(expected, given._set_tuple_undefined())

    @parameterized.expand(
        [
            (Descriptor(tuple[int, ...]), (Descriptor(tuple[int, ...]),)),
            (
                Descriptor(tuple[int]),
                (Descriptor(tuple[int]), Descriptor(tuple[int, ...])),
            ),
            (
                Descriptor(tuple[int, int]),
                (Descriptor(tuple[int, ...]), Descriptor(tuple[int, int])),
            ),
            (
                Descriptor(tuple[int, str]),
                (
                    Descriptor(tuple[int | str, ...]),
                    Descriptor(tuple[int, str]),
                ),
            ),
            (
                Descriptor(tuple[int, int, int]),
                (
                    Descriptor(tuple[int, ...]),
                    Descriptor(tuple[int, int, int]),
                ),
            ),
            (
                Descriptor(tuple[int, int, int, int]),
                (
                    Descriptor(tuple[int, ...]),
                    Descriptor(tuple[int, int, int, int]),
                ),
            ),
            (
                Descriptor(tuple[int, int, int, int]),
                (
                    Descriptor(tuple[int, ...]),
                    Descriptor(tuple[int, int, int, int]),
                ),
            ),
            (
                Descriptor(tuple[tuple[str, str], int]),
                (
                    Descriptor(tuple[tuple[str, str] | int, ...]),
                    Descriptor(tuple[tuple[str, ...], int]),
                    Descriptor(tuple[tuple[str, ...] | int, ...]),
                    Descriptor(tuple[tuple[str, str], int]),
                ),
            ),
            (
                Descriptor(list[tuple[str, str]]),
                (
                    Descriptor(list[tuple[str, str]]),
                    Descriptor(list[tuple[str, ...]]),
                ),
            ),
            (Descriptor(list[str]), (Descriptor(list[str]),)),
            (Descriptor(str), (Descriptor(str),)),
            (Descriptor(tuple), (Descriptor(tuple),)),
        ]
    )
    def test_undefined_tuple_combinations(
        self, given: Descriptor, expected: tuple[Descriptor]
    ) -> None:
        actual = given.undefined_tuple_combinations()
        self.assertEqual(
            set(expected),
            set(actual),
            {"given": given, "actual": actual, "expected": expected},
        )
