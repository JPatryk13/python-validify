from itertools import chain
from typing import Any
from src.type_hints import TypeInfo
from src.descriptor import Descriptor


def describe_type(__value: Any) -> Descriptor:
    _base_type = type(__value)
    if _base_type in [list, set, frozenset]:
        # single arg
        if len(__value) != 0:
            # has elements
            _args_types = [describe_type(elem) for elem in __value]
            if _args_types[1:] == _args_types[:-1]:
                # uniform-type collection
                return Descriptor(base=_base_type, args=(_args_types[0],))
            else:
                # multiple different types present in the collection
                return Descriptor(
                    base=_base_type,
                    args=(Descriptor(base=None, args=tuple(set(_args_types))),),
                )
        else:
            # empty collection
            return Descriptor(_base_type)

    elif _base_type == dict:
        # two args

        # I'm pretending here that dict_keys and dict_values are just regular
        # lists of values. This way I can easily get their TypeDescription
        # by extracting args from the result.
        return Descriptor(
            base=dict,
            args=(
                describe_type(list(__value.keys())).args[0],
                describe_type(list(__value.values())).args[0],
            ),
        )

    elif _base_type == tuple:
        return Descriptor(
            base=tuple, args=tuple([describe_type(elem) for elem in __value])
        )

    else:
        return Descriptor(_base_type)


def is_valid(__val: Any, __type_info: TypeInfo) -> bool:

    expected = Descriptor(__type_info)
    actual = describe_type(__val)

    actual_group = list(
        chain.from_iterable(
            [_td.undefined_tuple_combinations() for _td in actual.reductions()]
        )
    )

    return len(set(actual_group).intersection(set(expected.combinations()))) > 0
