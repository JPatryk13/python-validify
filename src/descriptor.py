from itertools import chain, combinations, product
from types import EllipsisType, GenericAlias, NoneType, UnionType
from typing import (
    Literal,
    TypeAlias,
    get_origin,
    get_args,
    overload,
    cast,
)

from src.type_hints import (
    SingleTypeInfo,
    SupportedBaseType,
    TypeInfo,
    WithUnion,
    is_subscriptable_base_type,
    is_supported_base_type,
    is_type_info,
    is_union,
)

_ArgsTuple: TypeAlias = "tuple[Descriptor, ...]"
_RawArgs: TypeAlias = (
    "tuple[TypeInfo | Descriptor, ...] | tuple[TypeInfo | Descriptor, EllipsisType]"
)


class Descriptor:
    """Provides a framework for working with `TypeInfo`.

    ### Examples - equivalence of initialization
    ```
    # using with SupportedBaseType
    Descriptor(int) == Descriptor(base=int)
    # using with NonUnionGeneric
    Descriptor(list[str]) == Descriptor(base=list args=(str,))
    # using with WithUnion (GenericAlias)
    Descriptor(tuple[str, str | int]) == \\
        Descriptor(base=tuple args=(str, str | int))
    # using with WithUnion (UnionType)
    Descriptor(str | list[str]) == Descriptor(args=(str, list[str]))
    # alternative notation
    Descriptor(str | list[str]) == \\
        Descriptor(args=(Descriptor(str), Descriptor(list[str])))
    ```
    """

    _args: _ArgsTuple
    _base: SupportedBaseType
    _raw: SingleTypeInfo | WithUnion
    _length: int | Literal["undefined"]
    _str: str
    parent: "Descriptor | None"

    @overload
    def __init__(
        self,
        __type_info: TypeInfo,
        *,
        _parent: "Descriptor | None" = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        base: SupportedBaseType | None = None,
        args: "_RawArgs | None" = None,
        _parent: "Descriptor | None" = None,
        _length: int | Literal["undefined"] | None = None,
    ) -> None: ...
    def __init__(
        self,
        __type_info: TypeInfo | None = None,
        *,
        base: SupportedBaseType | None = None,
        args: "_RawArgs | None" = None,
        _parent: "Descriptor | None" = None,
        _length: int | Literal["undefined"] | None = None,
    ) -> None:
        """
        Initializer provides two different ways of setting up `Descriptor` instance -
        see `Examples` for more info.

        ### Args
        - `__type_info` (`TypeInfo | None`, optional) - argument accepts only member of
        `TypeInfo`. Base and args are then inferred from it. When provided `base` and/or
        `args` keyword arguments cannot be given.
        - `base` (`SupportedBaseType | None`, optional) - E.g. for `list[str]` base would
        be `list`, for `str` base would be `str`, for `str | int` base would be `None`, etc.
        - `args` (`tuple[TypeInfo | Descriptor, ...] | None`, optional) - E.g. for
        `list[str]` args would be `(str,)`, for `str` args would be `None` (or empty tuple),
        for `str | int` args would be `(str | int,)` or `((str, int),)`, etc.

        ### Examples
        ```
        # implicit
        Descriptor(tuple[str, str | int])
        # explicit
        Descriptor(base=tuple, args=(str, str | int))
        # explicit - alternative
        Descriptor(base=tuple, args=(Descriptor(str), Descriptor(str | int)))
        Descriptor(base=tuple, args=(str, Descriptor(str | int)))
        # invalid
        Descriptor()
        Descriptor(list[int], base=list, args=(int,))
        ```

        ### Raises
        - `ValueError` when:
            - all arguments given
            - `__type_info` and `base` or `args` are given
        - `TypeError` when:
            - `__type_info` is not valid TypeInfo type
        """

        self.parent = _parent

        if (
            __type_info in [None, NoneType]
            and base in [None, NoneType]
            and args is None
        ):
            # expression of `None`
            self._base = None
            self._args = tuple()
            self._raw = None
            self._str = "None"

        elif __type_info is not None:
            # infer from the TypeInfo
            if is_type_info(__type_info):
                # valid TypeInfo
                if isinstance(__type_info, GenericAlias):
                    self._base = get_origin(__type_info)
                    self._args = tuple(
                        [
                            Descriptor(arg, _parent=self)
                            for arg in get_args(__type_info)
                            if arg != Ellipsis
                        ]
                    )
                    self._str = str(__type_info)
                    self._raw = __type_info

                elif isinstance(__type_info, (UnionType, tuple)):
                    self._base = None
                    _raw_args = (
                        __type_info
                        if isinstance(__type_info, tuple)
                        else get_args(__type_info)
                    )
                    self._args = tuple(
                        [Descriptor(arg, _parent=self) for arg in _raw_args]
                    )
                    self._str = " | ".join(arg._str for arg in self._args)
                    self._raw = eval(self._str)

                else:
                    # it's SupportedBaseType
                    self._base = __type_info
                    self._args = tuple()
                    # the inline if-stmt below mostly to satisfy pyright
                    self._str = (
                        __type_info.__name__ if __type_info is not None else "None"
                    )
                    self._raw = __type_info

            else:
                _msg = f"Invalid type of __type_info={__type_info}: `{type(__type_info).__name__}`."

                # adding some more detail regarding the type
                if isinstance(__type_info, tuple):
                    if len(__type_info) != 0:
                        _types = []
                        for member in __type_info:
                            _types.append(type(member).__name__)
                        _msg += (
                            f" More precisely the type is tuple[{', '.join(_types)}]"
                        )
                    else:
                        _msg += " The tuple is empty."

                raise TypeError(_msg)

        elif base is not None or args is not None:
            # use provided base and args
            if base is None or is_supported_base_type(base):
                self._base = base

            else:
                raise TypeError(
                    f"`base` argument must be type {SupportedBaseType}. Got {type(base)}"
                )

            if args is None or (isinstance(args, tuple) and len(args) == 0):
                # non-subscribed
                self._args = tuple()
                self._raw = base
                # the inline if-stmt below mostly to satisfy pyright
                self._str = base.__name__ if base is not None else "None"

            elif isinstance(args, tuple):
                # union (if base=None) or any other subscribed generic

                if self._base == tuple and len(args) == 2 and args[1] == Ellipsis:
                    # special case for tuple type with two args where the second one is "..."
                    self._args = (
                        (
                            args[0]
                            if isinstance(args[0], Descriptor)
                            else Descriptor(args[0], _parent=self)
                        ),
                    )

                elif all(
                    is_type_info(arg) or isinstance(arg, Descriptor) for arg in args
                ):
                    # in this scenarion ellipsis is not present in args
                    self._args = tuple(
                        (
                            arg
                            if isinstance(arg, Descriptor)
                            else Descriptor(cast(TypeInfo, arg), _parent=self)
                        )
                        for arg in args
                    )

                    # ensure that unions don't have muliple same arguments
                    if self._base is None:
                        self._args = tuple(set(self._args))
                        # as a result of removing duplicates in unions we may end up
                        # with a single element union
                        if len(self._args) == 1:
                            self._base = self._args[0].base
                            self._args = self._args[0].args
                            self._raw = self._args[0].raw
                            self._str = self._args[0]._str
                            # self._args = tuple()
                            # raise ValueError(
                            #     f"Only one unique argument, {self._args[0]}, found in the given {len(args)} args while base suggests the Descriptor is a union."
                            # )

                else:
                    raise TypeError(
                        f"Members of args must be {TypeInfo} or {Descriptor.__name__}"
                        f" type. Got tuple[{', '.join(type(arg).__name__ for arg in args)}]"
                    )

                # set `raw` based on given base and args
                if base is None:
                    # union
                    self._str = " | ".join(
                        cast(Descriptor, arg)._str for arg in self._args
                    )
                    self._raw = eval(self._str)

                else:
                    # generic
                    if ... in args:
                        # tuple with undefined number of elements
                        self._raw = base[  # pyright: ignore [reportGeneralTypeIssues]
                            self._args[0].raw, ...
                        ]
                        # due to some formatting issues have to do that string separately
                        self._str = f"tuple[{self._args[0]._str}, ...]"

                    else:
                        # general case - using self._args as it avoids dealing with different input types
                        self._raw = base[  # pyright: ignore [reportGeneralTypeIssues]
                            tuple(
                                arg.raw if isinstance(arg, Descriptor) else ...
                                for arg in self._args
                            )
                        ]
                        self._str = str(self._raw)

            else:
                raise TypeError(f"`args` must be a tuple or None. Got {type(args)}")

        else:
            # only either one can be given
            raise ValueError(
                "The input must be either type info or base and/or args, not both."
            )

        if _length is None:
            # determine length based on the base and args
            if (
                self.base == tuple
                and len(self._args) != 0
                and (... not in args if args is not None else True)
                and (
                    ... not in get_args(__type_info)
                    if __type_info is not None
                    else True
                )
            ):
                self._length = len(self.args)
            elif not is_subscriptable_base_type(self.base) or self.is_union:
                self._length = 1
            else:
                self._length = "undefined"

        else:
            if _length == "undefined":
                if self.base == tuple and len(self.args) > 1:
                    raise ValueError(
                        f'Setting _length to "undefined" while base is `tuple` and the number of arguments is greater than 1 is not allowed. Got {len(self.args)} args: {self.args}'
                    )
                elif not is_subscriptable_base_type(self.base) or self.is_union:
                    raise ValueError(
                        f"_length attribute must be 1 when the base is not subscriptable or the type description represents a union. Got _length={_length} while type description is {self}"
                    )

            else:
                if not (
                    self.base == tuple
                    or not is_subscriptable_base_type(self.base)
                    or self.is_union
                ):
                    raise ValueError(
                        f"Length can only be a defined integer for a tuple-based Descriptor, unions or non-subscriptables. Go"
                    )

                elif self.base == tuple and (
                    (args is not None and ... in args)
                    or (__type_info is not None and ... in get_args(__type_info))
                ):
                    raise ValueError(
                        f"Setting _length to a number (given: {_length}) while an ellipsis is within given arguments is not allowed."
                    )

                elif self.base == tuple and _length != len(self.args):
                    raise ValueError(
                        f"Provided _length ({_length}) does not match the number of given arguments ({len(self.args)})."
                    )

                elif (
                    not is_subscriptable_base_type(self.base) or self.is_union
                ) and _length != 1:
                    raise ValueError(
                        f"_length attribute must be 1 when the base is not subscriptable or the type description represents a union."
                    )

            # no errors raised
            self._length = _length

    @property
    def raw(self) -> SingleTypeInfo | WithUnion:
        """Type info (with tuples converted to unions).
        E.g. list[tuple[str, int] | dict[str, int]]"""
        return self._raw

    @property
    def base(self) -> SupportedBaseType:
        """Base of the type description. E.g. `list[str] -> base: list`,
        `str -> base: str`, `str | int -> base: None`."""
        return self._base

    @property
    def args(
        self,
    ) -> _ArgsTuple:
        """Arguments of the type description - each converted to `Descriptor`
        instance. E.g. `list[str] -> args: (str,)`, `str -> args: ()`,
        `str | int -> args: (str, int)`."""
        return self._args

    @property
    def no_args(self) -> "Descriptor | None":
        """Returns instance of `Descriptor` created only from the base.

        Example:
        ```
        Descriptor(list[str]).no_args.raw is list
        Descriptor(str | int).no_args is None
        Descriptor(None).no_args.raw is None
        ```
        """
        return Descriptor(self.base) if not self.is_union else None

    @property
    def depth(self) -> int:
        """Returns number of nested elements. I.e. how many levels of nesting the type has.

        Examples:
        ```
        Descriptor(list[tuple[str, str | list[str]]]).depth == 3
        Descriptor(list[tuple[str, str | int]]).depth == 2
        Descriptor(list[str]).depth == 1
        Descriptor(str | int).depth == 0
        Descriptor(str).depth == 0
        ```
        """

        if len(self.args) == 0:
            # no args = no depth
            return 0

        else:
            # aggregate all args across unions etc. E.g. (str, float | int) -> (str, float, int)
            _aggr_args: list[Descriptor] = []
            for arg in self.args:
                # skip ellipsis
                if arg is not ...:
                    if arg.is_union:
                        _aggr_args += [a for a in arg.args if a is not ...]

                    else:
                        _aggr_args.append(arg)

            # get depth for each argument
            _arg_depths = [arg.depth for arg in _aggr_args]

            if self.is_union:
                # union is treated as if it was multi-base Descriptor
                return max(_arg_depths)

            else:
                # adding 1 to account for the base
                return max(_arg_depths) + 1

    @property
    def length(self) -> int | Literal["undefined"]:
        return self._length

    @property
    def is_union(self) -> bool:
        """Union type. When this is True, other flags (`is_*`) are False."""
        return is_union(self.raw)

    def _remove_inner(
        self,
    ) -> "tuple[Descriptor, tuple[Descriptor, ...]]":
        """Removes the most inner type from the given `Descriptor`.

        Examples:
        ```
        _remove_inner(Descriptor( list[str | tuple[int, int]] )) == list[str | tuple], (int, int)
        _remove_inner(Descriptor( list[str | tuple] )) == list, (str | tuple,)
        _remove_inner(Descriptor( list )) == list, ()
        ```
        """
        if self.depth <= 1 and not self.is_union:
            # E.g. list[str] -> list
            return cast(Descriptor, self.no_args), self.args

        else:
            # E.g. tuple[str, list[int]] -> tuple[str, list]
            max_depth = max(arg.depth for arg in self.args)
            parent_args: list[Descriptor] = []
            remainder = []
            for arg in self.args:
                if getattr(arg, "depth", None) == max_depth:
                    p, r = arg._remove_inner()
                    parent_args.append(p)
                    remainder += list(r)
                else:
                    parent_args.append(arg)

            if self.base is None and len(set(parent_args)) == 1:
                # special case where we reduced from a union of subscribed
                # generics to a union of two alike arguments. E.g.:
                # tuple[str, int] | tuple[int] --> tuple | tuple
                # The above we want to convert to a single type description
                td = Descriptor(base=parent_args[0].base, args=parent_args[0].args)

            else:
                td = Descriptor(base=self.base, args=tuple(parent_args))

            return td, tuple(remainder)

    def reductions(self) -> "list[Descriptor]":
        reductions: list[Descriptor] = [self]
        while reductions[-1] != reductions[-1]._remove_inner()[0]:
            reductions.append(reductions[-1]._remove_inner()[0])
        return reductions

    def _group_args(self) -> "list[tuple[tuple[Descriptor, ...], ...]]":
        """Returns combinations of args of the type description as a list of groups.
        Each group is connected to a single argument. It is a tuple containing
        the combinations of the corresponding argument.

        Example #1:
        ```
        # instance args (base is not a tuple` or `None`)
        self = Descriptor( dict[int | float, str] )

        self._groupped_args() == [
            (
                (Descriptor( int ),),
                (Descriptor( float ),),
                (Descriptor( int ), Descriptor( float ))
            ),
            (
                (Descriptor( str ),),
            )
        ]
        ```

        Example #2:
        ```
        # instance args (base = tuple)
        self = Descriptor( tuple[int | float, str] )

        self._group_args() == [
            (
                (Descriptor( int ),),
                (Descriptor( float ),),
                (Descriptor( int ), Descriptor( float )),
            ),
            (
                (Descriptor( str ),),
            )
        ]
        ```
        """

        return [
            # Tuple contains all combinations for a particular argument or the argument
            # itself if no combinations given. Going from the inner-most list comprehension:
            #   -> calculate combinations for each arg (combinations of its arguments)
            #       -> join the collections of combinations (of those subargs)
            #           -> convert to tuple
            #               -> do the above for each argument
            (
                tuple(
                    chain.from_iterable(
                        combinations(arg.args, i + 1) for i in range(len(arg.args))
                    )
                )
                if arg.is_union
                else ((arg,),)
            )
            for arg in self.args
        ]

    def _transformed_groups(self) -> "list[Descriptor]":
        """Wraps aroung `_group_args()` method. Performs three transfromations:
        1a. Tuples with a single TD replaced with the inner TD
        1b. Tuples with multiple TDs replaced with a union that features inner TDs
        2. Calculate product of combinations
        3. Wrap each set of arguments in the TD featuring `self.base`
        """

        # trivial case - if the TD doesn't have args, it will not have any combinations
        if len(self.args) == 0:
            return [self]

        # _group_args method represents unions as tuples of multiple TDs. Below,
        # we transform those into unions. We also optionally exclude them, depending
        # on the base of the TD.
        unified: list[tuple[Descriptor]] = []

        # iterate over groups (each group corresponds to a single argument)
        for arg_combinations_group in self._group_args():
            sub_unif = []

            # iterate over different combinations and transform or exclude the union
            # tuples, and extract TDs from the tuples that contain only one element
            for cmb in arg_combinations_group:
                if len(cmb) > 1:
                    # it's a union
                    if not (
                        self.is_union
                        or (self.base == tuple and self.length != "undefined")
                    ):
                        # transform to a proper union
                        sub_unif.append(Descriptor(args=cmb, _parent=self.parent))
                else:
                    # non-union, pull out of the tuple
                    sub_unif.append(cmb[0])

            unified.append(tuple(sub_unif))

        # calculate product of combination groups. Example:
        #
        #   unified = [
        #       (
        #           Descriptor( list[str] ),
        #           Descriptor( list[int] ),
        #           Descriptor( list[str | int] )
        #       ), (
        #           Descriptor( str )
        #       )
        #   ]
        #   product(*unified) == [
        #       (
        #           Descriptor( list[str] ),
        #           Descriptor( str )
        #       ), (
        #           Descriptor( list[int] ),
        #           Descriptor( str )
        #       ), (
        #           Descriptor( list[str | int] ),
        #           Descriptor( str )
        #       )
        #   ]
        #
        # Then wraps each tuple in Descriptor featuring current TDs' base, E.g.:
        #
        #   return ... == [
        #       Descriptor( tuple[list[str], str] ),
        #       Descriptor( tuple[list[int], str] ),
        #       Descriptor( tuple[list[str | int], str] )
        #   ]
        return [
            Descriptor(base=self.base, args=p, _parent=self.parent, _length=self.length)
            for p in product(*unified)
        ]

    def combinations(self) -> "list[Descriptor]":

        if self.is_union and self.parent is None:
            # self is a union that has no parent
            # 1. find combinations of each member of the union
            # 2. flatten the iterable into a list of all possible combinations
            return list(chain.from_iterable(a.combinations() for a in self.args))

        elif len(self.args) > 0:
            # self might be a union with a parent or any other type description
            # with arguments
            _total_combinations = []

            # iterate over the combinations groups
            for combination in self._transformed_groups():
                sub_cmb_groups: list[list[Descriptor]] = []

                # iterate over each argument of the combination and add its combinations
                # to the list
                for cmb_arg in combination.args:
                    if cmb_arg.is_union:
                        # skip one level up
                        sub_cmb_groups.append(
                            [
                                Descriptor(args=p, _parent=self.parent)
                                for p in product(
                                    *[
                                        union_member.combinations()
                                        for union_member in cmb_arg.args
                                    ]
                                )
                            ]
                        )

                    else:
                        sub_cmb_groups.append(cmb_arg.combinations())

                # same as the last expression in _transformed_groupd()
                _total_combinations += [
                    Descriptor(
                        base=self.base, args=p, _parent=self.parent, _length=self.length
                    )
                    for p in product(*sub_cmb_groups)
                ]

            return _total_combinations

        else:
            # self has no arguments, therefore, has no combinations
            return [self]

    def _set_tuple_undefined(self) -> "Descriptor":
        if self.base == tuple and self.length != "undefined":
            if len(set(self.args)) == 1:
                # homogenous tuple e.g. tuple[int, int, int]
                _args = tuple(set(self.args))
            else:
                # non-homogenous e.g. tuple[int, int, str]
                _args = (Descriptor(args=tuple(set(self.args))),)
        else:
            _args = self.args

        return Descriptor(base=self.base, args=_args, _parent=self.parent)

    def undefined_tuple_combinations(self) -> "list[Descriptor]":
        modified_base_td: list[Descriptor] = [self, self._set_tuple_undefined()]
        modified_args = []
        for base_td in modified_base_td:
            for j, arg in enumerate(base_td.args):
                for cmb in arg.undefined_tuple_combinations():
                    _args_as_list = list(base_td.args)
                    _args_as_list[j] = cmb
                    modified_args.append(
                        Descriptor(
                            base=base_td.base,
                            args=tuple(_args_as_list),
                            _parent=base_td.parent,
                        )
                    )
        return list(set(modified_base_td).union(set(modified_args)))

    def __hash__(self) -> int:
        if self.is_union:
            return sum(hash(arg) for arg in self.args)
        else:
            return hash((self.base, self.args))

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Descriptor):
            return hash(self) == hash(__value)
        return False

    def __repr__(self) -> str:
        return f"Descriptor( {self._str} )"
