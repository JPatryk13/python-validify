# Validify

Python library for automated and manual runtime data type validation. It focuses on utilizing type hints and handling subscribed generics (e.g., `list[str]`). Use it manually with isvalid or add decorators to methods, functions, and classes for automatic validation.

While Python natively supports basic type validation, it does not manage complex types like `list[dict[str, tuple[str, str, bool]]]`. Validify simplifies this by allowing easy integration of type validation through a single decorator. Add it to your method or class, and let Validify ensure your type hints are enforced at runtime.

## Contents

&emsp;1 [Features](#1-features)<br>
&emsp;2 [Installation](#2-installation)<br>
&emsp;3 [Supported Data Types](#3-supported-data-types)<br>
&emsp;4 [Usage](#4-usage)<br>
&emsp;&emsp;4.1 [Manual validation](#41-manual-validation)<br>
&emsp;&emsp;4.2 [Decorator for Functions](#42-decorator-for-functions)<br>
&emsp;&emsp;4.3 [Decorator for Classes](#43-decorator-for-classes)<br>
&emsp;&emsp;4.4 [Notes](#44-notes)<br>
&emsp;5 [Developers Guide](#5-developers-guide)<br>
&emsp;&emsp;5.1 [Contributing](#51-contributing)<br>
&emsp;&emsp;5.2 [Architecture](#52-architecture)<br>
&emsp;&emsp;5.3 [Known Issues](#53-known-issues)<br>
&emsp;6 [License & Contact](#6-license--contact)<br>

## 1 Features

- Uniform way to describe and manipulate both base and generic data types via `Descriptor` class.
- Manual validation of data via `isvalid` function.
- Function signature inspection and input validation via `func.validate` decorator.
- Class-level attribute validation based on type annotations via `cls.validate` decorator.
- Class methods signature inspection and input validation via `cls.validate` decorator.
    

## 2 Installation

```python
pip install pyvalidify
```

## 3 Supported Data Types

- Text Type: `str`
- Numeric Types: `int`, `float`, `complex`
- Sequence Types: `list`, `tuple`, `range`
- Mapping Type: `dict`
- Set Types: `set`, `frozenset`
- Boolean Type: `bool`
- Binary Types: `bytes`, `bytearray`, `memoryview`
- None Type: `NoneType`/`None`
- Generics - e.g. `list[str]`
- Unions - e.g. `str | int`
- Generics with unions ([limited support](#3-bugs)) - e.g. `list | tuple[str | bytes, bool]`

## 4 Usage

### 4.1 Manual validation

```py
from validify import isvalid

simple_var = 2

isvalid(simple_var, int) # true
isvalid(simple_var, str) # false

complicated_var = [
    {
        "name": "John",
        "email": "johnny1975@hotmail.com"
    },
    {
        "name": "Dan",
        "email": None
    }
]

isvalid(complicated_var, list[dict[str, str]]) # false
isvalid(complicated_var, list[dict[str, str | None]]) # true
```

### 4.2 Decorator for Functions

```py
from validify import func

@func.validate
def func(a: list[int], b: list[int], *args: str, c: bool, **kwargs: bool) -> None: ...

func([1, 2, 3], [4, 5, 6], "foo", "bar", c=True, d=False) # OK
func((1, 2, 3), (4, 5, 6), "foo", "bar", c=True, d=False) # TypeError
```

### 4.3 Decorator for Classes

```py
from dataclasses import dataclass
from validify import cls

@dataclass
@cls.validify
class MyClass:
    name: str
    address: list[str]

MyClass("John", ["SY23 2JS", "3102 Bridge Street"]) # OK
MyClass("John", "SY23 2JS, 3102 Bridge Street") # TypeError

@cls.validify
class MyOtherClass:
    basket: list[tuple[str, int, float]]
    customer_name: str | None

    def __init__(self, **items: tuple[int, float]) -> None: ...

    def add_item(self, name: str, qty: int, price: float) -> None: ...

    @classmethod
    def from_item_list(cls, items: list[tuple[str, int, float]]) -> "MyOtherClass": ...

    @staticmethod
    def calcualte_total(item_prices: list[float]) -> float: ...

    @property
    def customer_name(self) -> str | None: ...

    @customer_name.setter
    def customer_name(self, val) -> None: ...

inst = MyOtherClass(chocolate=(1.5, 4.99)) # TypeError
inst.add_item("beans", "2", "2.59") # TypeError
inst = inst.from_item_list([["carrot", 5, 1.43], ["reduced fat pesto", 1, 2.99]]) # TypeError
total = MyOtherClass.calculate_total([("carrot", 5, 1.43), ("reduced fat pesto", 1, 2.99)]) # TypeError
inst.customer_name = ["Bart", "Simpson"] # TypeError
```

### 4.4 Notes

- `func.validate` does not work on lambdas and abstract methods (I guess the latter is no surprise).
- `classmethod` decorator must precede `func.validate`

## 5 Developers Guide

### 5.1 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes.
4. Push the branch to your fork.
5. Create a pull request.

### 5.2 Architecture

The library can be described as service based, however, it roughly follows layered, DDD-like pattern. The below names of each layer are mearely contextual - I made them up to remember what is what, don't judge. The rules of interactions of these layers are simple: a layer can only import from beneath itself.

**"service" layer #2:**
- `decorators.py` - two classes `cls` and `func` with static methods

**"service" layer #1:**
- `validator.py` - contains two functions: `describe_type()` - like Python's  native `type()` and `is_valid()` - like Python's native `isinstance()`

**"model" layer:**
- `descriptor.py` - definition of the `Descriptor` class, a framework for working with datatypes.

**"core" layer:**
- `type_hints.py` - describes supported types and defines functions for validating them.

### 5.3 Known Issues

- When describing a datatype in terms of combinations or their equivalence (see `type_description.TypeDescription.combinations()` or `type_description.TypeDescription.__hash__()`), unions are not being propagated outward within nested datatype. For example, consider a type `list[tuple[int | str]]`. It represents a list of tuples, where tuple can hold only one element each. Valid values would be `[(1,), (1,)]`, `[("1",), ("1",)]` or `[(1,), ("1",)]`. Respectively, they can be represented as types `list[tuple[int]]`, `list[tuple[str]]` or `list[tuple[int] | tuple[str]]`. The last expression is equivalent to the initial one - describes a list of mixed items. Unfortunately neither `combinations()` nor `__hash__()` method describe the the relationship. The issue is to be fixed.

## 6 License

Validify is licensed under the MIT License. See the [LICENSE](https://github.com/JPatryk13/validify/blob/main/LICENSE) file for more information.

