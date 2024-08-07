import asyncio
from dataclasses import dataclass, make_dataclass
from typing import Any, Generator
import unittest
from unittest.mock import patch

from src.validify.decorators import cls, func


class TestCaseWithMocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # start up patchers
        cls.is_valid_patcher = patch("src.validify.decorators.isvalid")
        cls.describe_type_patcher = patch("src.validify.decorators.describe_type")

        cls.is_valid_mock = cls.is_valid_patcher.start()
        cls.describe_type_mock = cls.describe_type_patcher.start()

    def setUp(self) -> None:
        self.is_valid_mock.reset_mock()
        # using regular isinstance instead of the validator
        self.is_valid_mock.side_effect = isinstance

        self.describe_type_mock.reset_mock()
        # mocking Descriptor with a simple dataclass to mimic the required
        # [by the decorator] `raw` property
        self.describe_type_mock.side_effect = lambda val: make_dataclass(
            "DescriptorMock", ["raw"]
        )(type(val))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.is_valid_patcher.stop()
        cls.describe_type_patcher.stop()


class TestDecoratorsFunc(TestCaseWithMocks):

    def test__map_args_to_kwargs_only_return_key_present(self) -> None:
        expected = {"foo": (str, "baz"), "bar": (int, 1)}
        actual = func._map_args_to_kwargs_only(
            annotations={"foo": str, "bar": int, "return": float},
            args=("baz",),
            kwargs={"bar": 1},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_no_annotations_no_args_and_kwargs(self) -> None:
        expected = {}
        actual = func._map_args_to_kwargs_only(
            annotations={},
            args=tuple(),
            kwargs={},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_no_annotations_args_given(self) -> None:
        expected = {}
        actual = func._map_args_to_kwargs_only(
            annotations={},
            args=("baz",),
            kwargs={},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_no_annotations_kwargs_given(self) -> None:
        expected = {}
        actual = func._map_args_to_kwargs_only(
            annotations={},
            args=tuple(),
            kwargs={"bar": 1},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_only_just_args(self) -> None:
        expected = {"foo": (str, "baz"), "bar": (int, 1)}
        actual = func._map_args_to_kwargs_only(
            annotations={"foo": str, "bar": int, "return": float},
            args=("baz", 1),
            kwargs={},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_only_just_kwargs(self) -> None:
        expected = {"foo": (str, "baz"), "bar": (int, 1)}
        actual = func._map_args_to_kwargs_only(
            annotations={"foo": str, "bar": int, "return": float},
            args=tuple(),
            kwargs={"foo": "baz", "bar": 1},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_only_missing_args(self) -> None:
        expected = {"bar": (int, 1)}
        actual = func._map_args_to_kwargs_only(
            annotations={"foo": str, "bar": int, "return": float},
            args=tuple(),
            kwargs={"bar": 1},
        )
        self.assertEqual(expected, actual)

    def test__map_args_to_kwargs_only_missing_kwargs(self) -> None:
        expected = {"foo": (str, "baz")}
        actual = func._map_args_to_kwargs_only(
            annotations={"foo": str, "bar": int, "return": float},
            args=("baz",),
            kwargs={},
        )
        self.assertEqual(expected, actual)

    def test_validate_func_without_args(self) -> None:

        @func.validate
        def _func() -> int:
            return 2 + 2

        self.assertEqual(_func(), 4)

    def test_validate_func_with_just_args_all_given(self) -> None:

        @func.validate
        def _func(foo: int, bar: list) -> list:
            return bar + [foo]

        # OK
        self.assertEqual(_func(1, [1, 2, 3]), [1, 2, 3, 1])

        with self.assertRaises(TypeError):
            _func(1, (1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func("a", [1, 2, 3, 4])  # pyright: ignore

    def test_validate_func_with_just_args_some_given(self) -> None:

        @func.validate
        def _func(foo: int, bar: list = []) -> list:
            return bar + [foo]

        # OK
        self.assertEqual(_func(1), [1])
        self.assertEqual(_func(1, [1, 2, 3]), [1, 2, 3, 1])

        with self.assertRaises(TypeError):
            _func("a")  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(1, (1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func("a", [1, 2, 3, 4])  # pyright: ignore

    def test_validate_func_with_just_args_none_given(self) -> None:

        @func.validate
        def _func(foo: int = 0, bar: list = []) -> list:
            return bar + [foo]

        # OK
        self.assertEqual(_func(), [0])
        self.assertEqual(_func(1), [1])
        self.assertEqual(_func(1, [1, 2, 3]), [1, 2, 3, 1])

        with self.assertRaises(TypeError):
            _func("a")  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(1, (1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func("a", [1, 2, 3, 4])  # pyright: ignore

    def test_validate_func_with_just_kwargs_all_given(self) -> None:

        @func.validate
        def _func(*, foo: int, bar: list) -> list:
            return bar + [foo]

        # OK
        self.assertEqual(_func(foo=1, bar=[1, 2, 3]), [1, 2, 3, 1])
        self.assertEqual(_func(bar=[1, 2, 3], foo=1), [1, 2, 3, 1])

        with self.assertRaises(TypeError):
            _func(foo=1, bar=(1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(bar=(1, 2, 3), foo=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(foo="a", bar=[1, 2, 3, 4])  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(
                bar=[1, 2, 3, 4],
                foo="a",  # pyright: ignore
            )

    def test_validate_func_with_just_kwargs_some_given(self) -> None:

        @func.validate
        def _func(*, foo: int, bar: list = []) -> list:
            return bar + [foo]

        # OK
        self.assertEqual(_func(foo=1, bar=[1, 2, 3]), [1, 2, 3, 1])
        self.assertEqual(_func(bar=[1, 2, 3], foo=1), [1, 2, 3, 1])
        self.assertEqual(_func(foo=1), [1])

        with self.assertRaises(TypeError):
            _func(foo="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(foo=1, bar=(1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(bar=(1, 2, 3), foo=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(foo="a", bar=[1, 2, 3, 4])  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(
                bar=[1, 2, 3, 4],
                foo="a",  # pyright: ignore
            )

    def test_validate_func_with_just_kwargs_none_given(self) -> None:

        @func.validate
        def _func(*, foo: int = 0, bar: list = []) -> list:
            return bar + [foo]

        # OK
        self.assertEqual(_func(foo=1, bar=[1, 2, 3]), [1, 2, 3, 1])
        self.assertEqual(_func(bar=[1, 2, 3], foo=1), [1, 2, 3, 1])
        self.assertEqual(_func(foo=1), [1])
        self.assertEqual(_func(), [0])

        with self.assertRaises(TypeError):
            _func(foo="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(foo=1, bar=(1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(bar=(1, 2, 3), foo=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(foo="a", bar=[1, 2, 3, 4])  # pyright: ignore

        with self.assertRaises(TypeError):
            _func(
                bar=[1, 2, 3, 4],
                foo="a",  # pyright: ignore
            )

    def test_validate_func_with_args_and_kwargs_all_given(self) -> None:

        @func.validate
        def _func(foo: int, *, bar: list, baz: float) -> list:
            return bar + [foo, baz]

        # OK
        self.assertEqual(_func(1, bar=[1, 2, 3], baz=0.0), [1, 2, 3, 1, 0.0])
        self.assertEqual(_func(1, baz=1.0, bar=[1, 2, 3]), [1, 2, 3, 1, 1.0])

        with self.assertRaises(TypeError):
            _func(
                1,
                bar=(1, 2, 3),  # pyright: ignore
                baz=2.0,
            )

        with self.assertRaises(TypeError):
            _func(
                "a",  # pyright: ignore
                bar=[1, 2, 3, 4],
                baz=2.0,
            )

        with self.assertRaises(TypeError):
            _func(
                1,
                bar=[1, 2, 3, 4],
                baz=(2.0,),  # pyright: ignore
            )

    def test_validate_func_with_args_and_kwargs_some_given(self) -> None:

        @func.validate
        def _func(foo: int = 1, *, bar: list = [], baz: float = 0.0) -> list:
            return bar + [foo, baz]

        # OK
        self.assertEqual(_func(1, bar=[1, 2, 3], baz=0.0), [1, 2, 3, 1, 0.0])
        self.assertEqual(_func(1, baz=1.0, bar=[1, 2, 3]), [1, 2, 3, 1, 1.0])
        self.assertEqual(_func(1, bar=[1, 2, 3]), [1, 2, 3, 1, 0.0])
        self.assertEqual(_func(1, baz=1.0), [1, 1.0])
        self.assertEqual(_func(baz=1.0), [1, 1.0])

        with self.assertRaises(TypeError):
            _func(
                1,
                bar=(1, 2, 3),  # pyright: ignore
                baz=2.0,
            )

        with self.assertRaises(TypeError):
            _func(
                "a",  # pyright: ignore
                bar=[1, 2, 3, 4],
                baz=2.0,
            )

        with self.assertRaises(TypeError):
            _func(
                1,
                bar=[1, 2, 3, 4],
                baz=(2.0,),  # pyright: ignore
            )

        with self.assertRaises(TypeError):
            _func(1, bar=(1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func("a")  # pyright: ignore

    def test_validate_func_with_args_and_kwargs_none_given(self) -> None:

        @func.validate
        def _func(foo: int = 1, *, bar: list = [], baz: float = 0.0) -> list:
            return bar + [foo, baz]

        # OK
        self.assertEqual(_func(1, bar=[1, 2, 3], baz=0.0), [1, 2, 3, 1, 0.0])
        self.assertEqual(_func(1, baz=1.0, bar=[1, 2, 3]), [1, 2, 3, 1, 1.0])
        self.assertEqual(_func(1, bar=[1, 2, 3]), [1, 2, 3, 1, 0.0])
        self.assertEqual(_func(1, baz=1.0), [1, 1.0])
        self.assertEqual(_func(baz=1.0), [1, 1.0])
        self.assertEqual(_func(), [1, 0.0])

        with self.assertRaises(TypeError):
            _func(
                1,
                bar=(1, 2, 3),  # pyright: ignore
                baz=2.0,
            )

        with self.assertRaises(TypeError):
            _func(
                "a",  # pyright: ignore
                bar=[1, 2, 3, 4],
                baz=2.0,
            )

        with self.assertRaises(TypeError):
            _func(
                1,
                bar=[1, 2, 3, 4],
                baz=(2.0,),  # pyright: ignore
            )

        with self.assertRaises(TypeError):
            _func(1, bar=(1, 2, 3))  # pyright: ignore

        with self.assertRaises(TypeError):
            _func("a")  # pyright: ignore

    def test_validate_func_with_implicit_args(self) -> None:

        @func.validate
        def _func(*args: str) -> str:
            return "".join(args)

        self.is_valid_mock.side_effect = lambda val, _: isinstance(val, tuple) and all(
            isinstance(v, str) for v in val
        )

        # OK
        self.assertEqual(_func(), "")
        self.assertEqual(_func("a"), "a")
        self.assertEqual(_func("a", "b", "c"), "abc")

        with self.assertRaises(TypeError):
            _func("a", 2, "c")  # pyright: ignore

    def test_validate_func_with_implicit_kwargs(self) -> None:

        @func.validate
        def _func(**kwargs: str) -> tuple[str, str]:
            return "".join(kwargs.keys()), "".join(kwargs.values())

        self.is_valid_mock.side_effect = lambda val, _: isinstance(val, dict) and all(
            isinstance(v, str) for v in val.values()
        )

        # OK
        self.assertEqual(_func(), ("", ""))
        self.assertEqual(_func(foo="a"), ("foo", "a"))
        self.assertEqual(_func(foo="a", bar="b", baz="c"), ("foobarbaz", "abc"))

        with self.assertRaises(TypeError):
            _func(foo="a", bar=2, baz="c")  # pyright: ignore

    def test_validate_instance_method(self) -> None:

        class Cls:
            def __init__(self) -> None:
                self.var = "bam"

            @func.validate
            def meth(self, foo: int, *, bar: str, baz: float = 0.0) -> str:
                return str(foo) + str(baz) + bar + self.var

        # OK
        self.assertEqual(Cls().meth(1, bar="a"), "10.0abam")
        self.assertEqual(Cls().meth(1, bar="a", baz=1.0), "11.0abam")

        with self.assertRaises(TypeError):
            Cls().meth("a", bar="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls().meth(1, bar=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls().meth(1, bar="a", baz="a")  # pyright: ignore

    def test_validate_class_method(self) -> None:

        class Cls:
            var = "x"

            def __init__(self) -> None:
                self.var = "y"

            @classmethod
            @func.validate
            def meth(cls, foo: int, *, bar: str, baz: float = 0.0) -> str:
                return str(foo) + str(baz) + bar + cls.var

        # OK
        self.assertEqual(Cls.meth(1, bar="a"), "10.0ax")
        self.assertEqual(Cls.meth(1, bar="a", baz=1.0), "11.0ax")

        with self.assertRaises(TypeError):
            Cls().meth("a", bar="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls().meth(1, bar=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls().meth(1, bar="a", baz="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth("a", bar="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth(1, bar=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth(1, bar="a", baz="a")  # pyright: ignore

    def test_validate_above_static_method_decorator(self) -> None:

        class Cls:
            var = "x"

            @func.validate
            @staticmethod
            def meth(foo: int, *, bar: str, baz: float = 0.0) -> str:
                return str(foo) + str(baz) + bar + Cls.var

        # OK
        self.assertEqual(Cls.meth(1, bar="a"), "10.0ax")
        self.assertEqual(Cls.meth(1, bar="a", baz=1.0), "11.0ax")

        with self.assertRaises(TypeError):
            Cls.meth("a", bar="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth(1, bar=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth(1, bar="a", baz="a")  # pyright: ignore

    def test_validate_below_static_method_decorator(self) -> None:

        class Cls:
            var = "x"

            @staticmethod
            @func.validate
            def meth(foo: int, *, bar: str, baz: float = 0.0) -> str:
                return str(foo) + str(baz) + bar + Cls.var

        # OK
        self.assertEqual(Cls.meth(1, bar="a"), "10.0ax")
        self.assertEqual(Cls.meth(1, bar="a", baz=1.0), "11.0ax")

        with self.assertRaises(TypeError):
            Cls.meth("a", bar="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth(1, bar=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls.meth(1, bar="a", baz="a")  # pyright: ignore

    def test_validate_constructor(self) -> None:

        class Cls:
            @func.validate
            def __init__(self, foo: int, *, bar: str, baz: float = 0.0) -> None:
                self.fooz = foo + baz
                self.bar = bar

        # OK
        inst1 = Cls(1, bar="a")
        self.assertIsInstance(inst1, Cls)
        self.assertEqual(inst1.fooz, 1.0)
        self.assertEqual(inst1.bar, "a")

        # OK
        inst2 = Cls(1, bar="a", baz=1.0)
        self.assertIsInstance(inst2, Cls)
        self.assertEqual(inst2.fooz, 2.0)
        self.assertEqual(inst2.bar, "a")

        with self.assertRaises(TypeError):
            Cls("a", bar="a")  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls(1, bar=1)  # pyright: ignore

        with self.assertRaises(TypeError):
            Cls(1, bar="a", baz="a")  # pyright: ignore

    def test_validate_property_setter(self) -> None:

        class Cls:
            @property
            def prop(self) -> int:
                return self._prop

            @prop.setter
            @func.validate
            def prop(self, val: int) -> None:
                self._prop = val

        # OK
        inst = Cls()
        inst.prop = 1
        self.assertEqual(inst.prop, 1)

        with self.assertRaises(TypeError):
            Cls().prop = "a"  # pyright: ignore

    def test_validate_async_function(self) -> None:

        @func.validate
        async def _func(
            foo: int = 0, *, bar: str | None = None, baz: float = 0.0
        ) -> str:
            return str(foo) + str(bar) + str(baz)

        # OK
        self.assertEqual(asyncio.run(_func()), "0None0.0")
        self.assertEqual(asyncio.run(_func(1)), "1None0.0")
        self.assertEqual(asyncio.run(_func(1, bar="a")), "1a0.0")
        self.assertEqual(asyncio.run(_func(1, bar="a", baz=1.5)), "1a1.5")

        with self.assertRaises(TypeError):
            asyncio.run(_func("1"))  # pyright: ignore

        with self.assertRaises(TypeError):
            asyncio.run(_func(bar=1))  # pyright: ignore

        with self.assertRaises(TypeError):
            asyncio.run(_func(baz="1.5"))  # pyright: ignore

    def test_validate_generator(self) -> None:

        @func.validate
        def _func(lim: int) -> Generator[int, Any, None]:
            for i in range(lim):
                yield i

        # OK
        g = _func(5)
        self.assertEqual(list(g), [0, 1, 2, 3, 4])
        g.close()

        with self.assertRaises(TypeError):
            _func([1, 2, 3])  # pyright: ignore

    def test_validate_async_generator(self) -> None:

        @func.validate
        async def _gen(lim: int):
            for i in range(lim):
                yield i

        async def _func(lim: int):
            g = _gen(lim)
            ls = [i async for i in g]
            await g.aclose()
            return ls

        # OK
        self.assertEqual(list(asyncio.run(_func(5))), [0, 1, 2, 3, 4])

        with self.assertRaises(TypeError):
            asyncio.run(_func([1, 2, 3]))  # pyright: ignore


class TestDecoratorsCls(TestCaseWithMocks):

    def test_validate_child_class_with_owned_and_inherited_instance_method(self):
        class Parent:
            "Parent"

            def parent_meth(self, attr: int) -> int:
                return attr

        @cls.validate
        class Child(Parent):
            "Child"

            def child_meth(self, attr: int) -> int:
                return attr

        # OK
        self.assertEqual(Child().child_meth(5), 5)
        self.assertEqual(Child().parent_meth(5), 5)
        self.assertEqual(Parent().parent_meth(5), 5)
        self.assertEqual(Parent().parent_meth("5"), "5")  # pyright: ignore

        with self.assertRaises(TypeError):
            Child().child_meth("5")  # pyright: ignore

        with self.assertRaises(TypeError):
            Child().parent_meth("5")  # pyright: ignore

    def test_validate_child_class_with_owned_and_inherited_staticmethod(self):
        class Parent:
            @staticmethod
            def parent_meth(attr: int) -> int:
                return attr

        @cls.validate
        class Child(Parent):
            @staticmethod
            def child_meth(attr: int) -> int:
                return attr

        # OK
        self.assertEqual(Child.child_meth(5), 5)
        self.assertEqual(Child.parent_meth(5), 5)
        self.assertEqual(Parent.parent_meth(5), 5)
        self.assertEqual(Parent.parent_meth("5"), "5")  # pyright: ignore

        with self.assertRaises(TypeError):
            Child.child_meth("5")  # pyright: ignore

        with self.assertRaises(TypeError):
            Child.parent_meth("5")  # pyright: ignore

    def test_validate_child_class_with_owned_and_inherited_classmethod(self):
        class Parent:
            @classmethod
            def parent_meth(cls, attr: int) -> int:
                return attr

        @cls.validate
        class Child(Parent):
            @classmethod
            def child_meth(cls, attr: int) -> int:
                return attr

        # OK
        self.assertEqual(Child.child_meth(5), 5)
        self.assertEqual(Child.parent_meth(5), 5)
        self.assertEqual(Parent.parent_meth(5), 5)
        self.assertEqual(Parent.parent_meth("5"), "5")  # pyright: ignore

        with self.assertRaises(TypeError):
            Child.child_meth("5")  # pyright: ignore

        with self.assertRaises(TypeError):
            Child.parent_meth("5")  # pyright: ignore

    def test_validate_child_class_with_owned_and_inherited_explicit_property_setter(
        self,
    ):
        class Parent:

            @property
            def parent_property(self) -> int:
                return self._parent_property

            @parent_property.setter
            def parent_property(self, val: int) -> None:
                self._parent_property = val

        @cls.validate
        class Child(Parent):

            @property
            def child_property(self) -> int:
                return self._child_property

            @child_property.setter
            def child_property(self, val: int) -> None:
                self._child_property = val

        # OK
        c = Child()
        c.parent_property = 5
        self.assertEqual(c.parent_property, 5)
        c.child_property = 5
        self.assertEqual(c.child_property, 5)
        p = Parent()
        p.parent_property = 5
        self.assertEqual(p.parent_property, 5)
        p.parent_property = "5"  # pyright: ignore
        self.assertEqual(p.parent_property, "5")

        with self.assertRaises(TypeError):
            Child().child_property = "5"  # pyright: ignore

        with self.assertRaises(TypeError):
            Child().parent_property = "5"  # pyright: ignore

    def test_validate_child_class_with_owned_and_inherited_implicit_property_setter(
        self,
    ):
        class Parent:
            parent_property: int

        @cls.validate
        class Child(Parent):
            child_property: int

        # OK
        c = Child()
        c.parent_property = 5
        self.assertEqual(c.parent_property, 5)
        c.child_property = 5
        self.assertEqual(c.child_property, 5)
        p = Parent()
        p.parent_property = 5
        self.assertEqual(p.parent_property, 5)
        p.parent_property = "5"  # pyright: ignore
        self.assertEqual(p.parent_property, "5")

        with self.assertRaises(TypeError):
            Child().child_property = "5"  # pyright: ignore

        with self.assertRaises(TypeError):
            Child().parent_property = "5"  # pyright: ignore

    def test_validate_child_class_with_owned_and_inherited_dataclass_constructor(self):
        @dataclass
        class Parent:
            parent_property: int

        @cls.validate
        @dataclass
        class Child(Parent):
            child_property: int

        # OK
        c = Child(5, 5)
        c.parent_property = 3
        self.assertEqual(c.parent_property, 3)
        c.child_property = 3
        self.assertEqual(c.child_property, 3)
        p = Parent(5)
        Parent("p")  # pyright: ignore
        p.parent_property = 5
        self.assertEqual(p.parent_property, 5)
        p.parent_property = "5"  # pyright: ignore
        self.assertEqual(p.parent_property, "5")

        with self.assertRaises(TypeError):
            Child(5, 5).child_property = "5"  # pyright: ignore

        with self.assertRaises(TypeError):
            Child(5, 5).parent_property = "5"  # pyright: ignore

        with self.assertRaises(TypeError):
            Child("5", 5)  # pyright: ignore

        with self.assertRaises(TypeError):
            Child(5, "5")  # pyright: ignore
