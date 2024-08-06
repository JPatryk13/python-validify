from pprint import pformat
import unittest

from src.tree import Tree, TreeDict


class TestTree(unittest.TestCase):
    def test_init_with_just_parent(self) -> None:
        parent = "foo"
        tree = Tree(parent)
        self.assertEqual(parent, tree.parent)
        self.assertEqual([], tree.nodes)

    def test_init_with_parent_and_nodes(self) -> None:
        parent = "foo"
        nodes = [Tree("bar")]
        tree = Tree(parent, nodes)
        self.assertEqual(parent, tree.parent)
        self.assertEqual(1, len(tree.nodes))
        self.assertEqual(nodes[0].parent, tree.nodes[0].parent)

    def test_init_invalid_node_type_raises_error(self) -> None:
        parent = "foo"
        nodes = ["bar"]
        with self.assertRaises(TypeError):
            _ = Tree(parent, nodes)  # type: ignore

    def test_init_without_arguments_raises_error(self) -> None:
        with self.assertRaises(TypeError):
            _ = Tree()  # type: ignore

    def test_from_dict_and_to_dict(self) -> None:
        parent = "foo"
        nodes = [Tree("bar")]
        _dict = TreeDict(parent="foo", nodes=[TreeDict(parent="bar", nodes=[])])
        _inst = Tree(parent, nodes)
        _inst_from_dict = Tree.from_dict(_dict)
        self.assertEqual(_inst.parent, _inst_from_dict.parent)
        self.assertEqual(
            1,
            len(_inst_from_dict.nodes),
            pformat({"instance": _inst_from_dict, "nodes": _inst_from_dict.nodes}),
        )
        self.assertEqual(_inst.nodes[0].parent, _inst_from_dict.nodes[0].parent)
        _dict_from_inst = _inst_from_dict.to_dict()
        self.assertEqual(
            {"parent": "foo", "nodes": [{"parent": "bar"}]}, _dict_from_inst
        )

    def test_add_node(self) -> None:
        tree = Tree("foo")
        tree.add_node(Tree("bar"))
        self.assertEqual(1, len(tree.nodes))
        self.assertEqual("bar", tree.nodes[0].parent)

    def test_add_node_invalid_value_raises_error(self) -> None:
        tree = Tree("foo")
        with self.assertRaises(TypeError):
            _ = tree.add_node("bar")  # type: ignore

    def test_root_depth_property(self) -> None:
        tree = Tree(
            "grandparent",
            [
                Tree("parent1", [Tree("child11")]),
                Tree(
                    "parent2",
                    [
                        Tree("child21", [Tree("grandchild211"), Tree("grandchild212")]),
                        Tree("child22", [Tree("grandchild221")]),
                    ],
                ),
                Tree(
                    "parent3",
                    [Tree("child31"), Tree("child32", [Tree("grandchild321")])],
                ),
            ],
        )
        self.assertEqual(0, tree.root_depth)
        for node in tree.nodes:
            self.assertEqual(1, node.root_depth)
            for subnode in node.nodes:
                self.assertEqual(2, subnode.root_depth)
                for subsubnode in subnode.nodes:
                    self.assertEqual(3, subsubnode.root_depth)

    def test_pformat(self) -> None:
        tree = Tree(
            "grandparent",
            [
                Tree("parent1", [Tree("child11")]),
                Tree("parent2", [Tree("child21"), Tree("child22")]),
                Tree(
                    "parent3",
                    [Tree("child31"), Tree("child32", [Tree("grandchild321")])],
                ),
            ],
        )
        expected_non_compact = (
            "grandparent"
            "\n|"
            "\n|___ parent1"
            "\n|    |"
            "\n|    |___ child11"
            "\n|"
            "\n|___ parent2"
            "\n|    |"
            "\n|    |___ child21"
            "\n|    |"
            "\n|    |___ child22"
            "\n|"
            "\n|___ parent3"
            "\n     |"
            "\n     |___ child31"
            "\n     |"
            "\n     |___ child32"
            "\n          |"
            "\n          |___ grandchild321"
        )
        self.assertListEqual(
            expected_non_compact.split("\n"), tree.pformat().split("\n")
        )

        expected_compact = (
            "grandparent"
            "\n|___ parent1"
            "\n|    |___ child11"
            "\n|___ parent2"
            "\n|    |___ child21"
            "\n|    |___ child22"
            "\n|___ parent3"
            "\n     |___ child31"
            "\n     |___ child32"
            "\n          |___ grandchild321"
        )
        self.assertListEqual(
            expected_compact.split("\n"), tree.pformat(compact=True).split("\n")
        )
