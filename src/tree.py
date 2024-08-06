import __future__
from typing import TypedDict, Any


class TreeDict(TypedDict, total=False):
    parent: Any
    nodes: "list[TreeDict]"


class Tree:
    parent: Any
    nodes: "list[Tree]"
    _root_depth: int | None

    def __init__(self, parent: Any, nodes: "list[Tree]" = [], **kwargs: Any) -> None:
        self._root_depth = None
        self.parent = parent
        if len(nodes) != 0:
            if all(isinstance(n, Tree) for n in nodes):
                self.nodes = nodes
            else:
                raise TypeError(
                    "At least one member of the `nodes` arg is not an instance of the `Tree` class."
                )
        else:
            self.nodes = []

    def __get_pformat_base(
        self, *, skip_pipe_symbols_at_level: list, compact: bool
    ) -> str:
        """Create string representation of the current line and - if the compact
        set to False - the line above. See `_pformat` for the explanation of the
        `skip_pipe_symbols_at_level`.

        Examples:
        ```
        # compact = False, self.root_depth = 2, skip_pipe_symbols_at_level = []
        '''
        |    |    |
        |    |    |___ <parent>
        '''
        # compact = False, self.root_depth = 3, skip_pipe_symbols_at_level = [1,2]
        '''
        |              |
        |              |___ <parent>
        '''
        # compact = False, self.root_depth = 2, skip_pipe_symbols_at_level = []
        '''
             |    |___ <parent>
        '''
        ```
        """
        if self.root_depth == 0:
            return str(self.parent)
        else:
            skeleton = (4 * " ").join(
                [
                    "|" if i not in skip_pipe_symbols_at_level else " "
                    for i in range(self.root_depth)
                ]
            )
            if compact:
                return skeleton + f"___ {self.parent}"
            else:
                return skeleton + "\n" + skeleton + f"___ {self.parent}"

    def __get_pformat_branches(
        self, *, is_last_child: bool, skip_pipe_symbols_at_level: list, compact: bool
    ) -> str:
        _skip_pipe_symbols_at_level = (
            skip_pipe_symbols_at_level + [self.root_depth - 1] if is_last_child else []
        )
        return "".join(
            [
                n._pformat(
                    is_last_child=(i == (len(self.nodes) - 1)),
                    skip_pipe_symbols_at_level=_skip_pipe_symbols_at_level,
                    compact=compact,
                )
                for i, n in enumerate(self.nodes)
            ]
        )

    def _pformat(
        self,
        *,
        is_last_child: bool,
        skip_pipe_symbols_at_level: list[int],
        compact: bool,
    ) -> str:
        """Underlying method for creating string representation of the tree.

        Args:
            - `is_last_child` (`bool`) - is the node (instance of the Tree
            this method belongs to) last one in the list of nodes?
            - `skip_pipe_symbols_at_level` (`list[int]`) - e.g. the instance
            this method belongs to is the last child of the root parent,
            therefore, `skip_pipe_symbols_at_level=[0]`

        Example:
        ```
        '''
        root
        |
        ...
        |
        |___ parent  <---- last child of the `root`
            |            - skip pipe #0
            |___ child1  - skip pipe #0
            |            - skip pipe #0
            |___ child2  <---- last child of the `parent`, skip pipe #0
                |        - skip pipes #0, #1
                |___ grandchild  <---- last child of the `child2`, skip pipes #0, #1
        '''
        ```
        """
        return (
            self.__get_pformat_base(
                skip_pipe_symbols_at_level=skip_pipe_symbols_at_level, compact=compact
            )
            + "\n"
            + self.__get_pformat_branches(
                is_last_child=is_last_child,
                skip_pipe_symbols_at_level=skip_pipe_symbols_at_level,
                compact=compact,
            )
        )

    def pformat(self, compact: bool = False) -> str:
        """Returns a multiline string representation of the tree.

        Args:
            - `compact` (`bool`, optional) - when set to True, each subsequent
            child takes up only a single line instead of two. See examples for
            more info. (default: `False`)

        Examples:
        ```
        tree = Tree(
            "parent",
            [Tree("child1"), Tree("child2", [Tree("subchild")])],
        )
        tree.pformat() -> (
            "\\nparent"
            "\\n|"
            "\\n|___ child1"
            "\\n|"
            "\\n|___ child2"
            "\\n    |"
            "\\n    |___ subchild"
        )
        tree.pformat(compact=True) -> (
            "\\nparent"
            "\\n|___ child1"
            "\\n|___ child2"
            "\\n    |___ subchild"
        )
        ```
        """
        return self._pformat(
            is_last_child=False, skip_pipe_symbols_at_level=[], compact=compact
        ).strip()

    @property
    def root_depth(self) -> int:
        if self._root_depth is None:
            self._root_depth = 0

        for node in self.nodes:
            node._root_depth = self._root_depth + 1
            node.root_depth  # recursive call

        return self._root_depth

    def add_node(self, __node: "Tree") -> "Tree":
        if isinstance(__node, Tree):
            self.nodes.append(__node)
            return self
        else:
            raise TypeError(f"Invalid type of the node. Got {type(__node)}")

    @classmethod
    def from_dict(cls, __dict: TreeDict) -> "Tree":
        tree = cls(
            __dict["parent"]  # pyright: ignore [reportTypedDictNotRequiredAccess]
        )
        tree.nodes = [cls.from_dict(node) for node in __dict.get("nodes", [])]
        return tree

    def to_dict(self) -> TreeDict:
        return self.__dict__

    def to_set(self) -> set[Any]:
        return {self.parent}.union(*(n.to_set() for n in self.nodes))

    @property
    def __dict__(self) -> TreeDict:
        if len(self.nodes) == 0:
            return {"parent": self.parent}
        else:
            return {
                "parent": self.parent,
                "nodes": [node.__dict__ for node in self.nodes],
            }

    def __repr__(self) -> str:
        return f"Tree(parent: {self.parent}, nodes_count: {len(self.nodes)})"
