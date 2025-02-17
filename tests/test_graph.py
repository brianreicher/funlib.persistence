from funlib.geometry import Roi, Coordinate

import networkx as nx
import pytest


def test_graph_filtering(provider_factory):
    graph_writer = provider_factory("w")
    roi = Roi((0, 0, 0), (10, 10, 10))
    graph = graph_writer[roi]

    graph.add_node(2, position=(2, 2, 2), selected=True)
    graph.add_node(42, position=(1, 1, 1), selected=False)
    graph.add_node(23, position=(5, 5, 5), selected=True)
    graph.add_node(57, position=Coordinate((7, 7, 7)), selected=True)
    graph.add_edge(42, 23, selected=False)
    graph.add_edge(57, 23, selected=True)
    graph.add_edge(2, 42, selected=True)

    graph.write_nodes()
    graph.write_edges()

    graph_reader = provider_factory("r")

    filtered_nodes = graph_reader.read_nodes(roi, attr_filter={"selected": True})
    filtered_node_ids = [node["id"] for node in filtered_nodes]
    expected_node_ids = [2, 23, 57]
    assert expected_node_ids == filtered_node_ids

    filtered_edges = graph_reader.read_edges(roi, attr_filter={"selected": True})
    filtered_edge_endpoints = [(edge["u"], edge["v"]) for edge in filtered_edges]
    expected_edge_endpoints = [(57, 23), (2, 42)]
    for u, v in expected_edge_endpoints:
        assert (u, v) in filtered_edge_endpoints or (v, u) in filtered_edge_endpoints

    filtered_subgraph = graph_reader.get_graph(
        roi, nodes_filter={"selected": True}, edges_filter={"selected": True}
    )
    nodes_with_position = [
        node for node, data in filtered_subgraph.nodes(data=True) if "position" in data
    ]
    assert expected_node_ids == nodes_with_position
    assert len(filtered_subgraph.edges()) == len(expected_edge_endpoints)
    for u, v in expected_edge_endpoints:
        assert (u, v) in filtered_subgraph.edges() or (
            v,
            u,
        ) in filtered_subgraph.edges()


def test_graph_filtering_complex(provider_factory):
    graph_provider = provider_factory("w")
    roi = Roi((0, 0, 0), (10, 10, 10))
    graph = graph_provider[roi]

    graph.add_node(2, position=(2, 2, 2), selected=True, test="test")
    graph.add_node(42, position=(1, 1, 1), selected=False, test="test2")
    graph.add_node(23, position=(5, 5, 5), selected=True, test="test2")
    graph.add_node(57, position=Coordinate((7, 7, 7)), selected=True, test="test")

    graph.add_edge(42, 23, selected=False, a=100, b=3)
    graph.add_edge(57, 23, selected=True, a=100, b=2)
    graph.add_edge(2, 42, selected=True, a=101, b=3)

    graph.write_nodes()
    graph.write_edges()

    graph_provider = provider_factory("r")

    filtered_nodes = graph_provider.read_nodes(
        roi, attr_filter={"selected": True, "test": "test"}
    )
    filtered_node_ids = [node["id"] for node in filtered_nodes]
    expected_node_ids = [2, 57]
    assert expected_node_ids == filtered_node_ids

    filtered_edges = graph_provider.read_edges(
        roi, attr_filter={"selected": True, "a": 100}
    )
    filtered_edge_endpoints = [(edge["u"], edge["v"]) for edge in filtered_edges]
    expected_edge_endpoints = [(57, 23)]
    for u, v in expected_edge_endpoints:
        assert (u, v) in filtered_edge_endpoints or (v, u) in filtered_edge_endpoints

    filtered_subgraph = graph_provider.get_graph(
        roi,
        nodes_filter={"selected": True, "test": "test"},
        edges_filter={"selected": True, "a": 100},
    )
    nodes_with_position = [
        node for node, data in filtered_subgraph.nodes(data=True) if "position" in data
    ]
    assert expected_node_ids == nodes_with_position
    assert len(filtered_subgraph.edges()) == 0


def test_graph_read_and_update_specific_attrs(provider_factory):
    graph_provider = provider_factory("w")
    roi = Roi((0, 0, 0), (10, 10, 10))
    graph = graph_provider[roi]

    graph.add_node(2, position=(2, 2, 2), selected=True, test="test")
    graph.add_node(42, position=(1, 1, 1), selected=False, test="test2")
    graph.add_node(23, position=(5, 5, 5), selected=True, test="test2")
    graph.add_node(57, position=Coordinate((7, 7, 7)), selected=True, test="test")

    graph.add_edge(42, 23, selected=False, a=100, b=3)
    graph.add_edge(57, 23, selected=True, a=100, b=2)
    graph.add_edge(2, 42, selected=True, a=101, b=3)

    graph.write_nodes()
    graph.write_edges()

    graph_provider = provider_factory("r+")
    limited_graph = graph_provider.get_graph(
        roi, node_attrs=["selected"], edge_attrs=["c"]
    )

    for node, data in limited_graph.nodes(data=True):
        assert "test" not in data
        assert "selected" in data
        data["selected"] = True

    for u, v, data in limited_graph.edges(data=True):
        assert "a" not in data
        assert "b" not in data
        nx.set_edge_attributes(limited_graph, 5, "c")

    limited_graph.update_edge_attrs(attributes=["c"])
    limited_graph.update_node_attrs(attributes=["selected"])

    updated_graph = graph_provider.get_graph(roi)

    for node, data in updated_graph.nodes(data=True):
        assert data["selected"]

    for u, v, data in updated_graph.edges(data=True):
        assert data["c"] == 5


def test_graph_read_unbounded_roi(provider_factory):
    graph_provider = provider_factory("w")
    roi = Roi((0, 0, 0), (10, 10, 10))
    unbounded_roi = Roi((None, None, None), (None, None, None))

    graph = graph_provider[roi]

    graph.add_node(2, position=(2, 2, 2), selected=True, test="test")
    graph.add_node(42, position=(1, 1, 1), selected=False, test="test2")
    graph.add_node(23, position=(5, 5, 5), selected=True, test="test2")
    graph.add_node(57, position=Coordinate((7, 7, 7)), selected=True, test="test")

    graph.add_edge(42, 23, selected=False, a=100, b=3)
    graph.add_edge(57, 23, selected=True, a=100, b=2)
    graph.add_edge(2, 42, selected=True, a=101, b=3)

    graph.write_nodes()
    graph.write_edges()

    graph_provider = provider_factory("r+")
    limited_graph = graph_provider.get_graph(
        unbounded_roi, node_attrs=["selected"], edge_attrs=["c"]
    )

    seen = []
    for node, data in limited_graph.nodes(data=True):
        assert "test" not in data
        assert "selected" in data
        data["selected"] = True
        seen.append(node)

    assert seen == [2, 42, 23, 57]


def test_graph_read_meta_values(provider_factory):
    roi = Roi((0, 0, 0), (10, 10, 10))
    provider_factory("w", True, roi)
    graph_provider = provider_factory("r", None, None)
    assert True == graph_provider.directed
    assert roi == graph_provider.total_roi


def test_graph_default_meta_values(provider_factory):
    provider = provider_factory("w", None, None)
    assert False == provider.directed
    assert provider.total_roi is None
    graph_provider = provider_factory("r", None, None)
    assert False == graph_provider.directed
    assert graph_provider.total_roi is None


def test_graph_nonmatching_meta_values(provider_factory):
    roi = Roi((0, 0, 0), (10, 10, 10))
    roi2 = Roi((1, 0, 0), (10, 10, 10))
    provider_factory("w", True, None)
    with pytest.raises(ValueError):
        provider_factory("r", False, None)
    provider_factory("w", None, roi)
    with pytest.raises(ValueError):
        provider_factory("r", None, roi2)


def test_graph_io(provider_factory):
    graph_provider = provider_factory("w")

    graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(42, 23)
    graph.add_edge(57, 23)
    graph.add_edge(2, 42)

    graph.write_nodes()
    graph.write_edges()

    graph_provider = provider_factory("r")
    compare_graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    nodes = sorted(list(graph.nodes()))
    nodes.remove(2)  # node 2 has no position and will not be queried
    compare_nodes = sorted(list(compare_graph.nodes()))

    edges = sorted(list(graph.edges()))
    edges.remove((2, 42))  # node 2 has no position and will not be queried
    compare_edges = sorted(list(compare_graph.edges()))

    assert nodes == compare_nodes
    assert edges == compare_edges


def test_graph_fail_if_exists(provider_factory):
    graph_provider = provider_factory("w")
    graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(42, 23)
    graph.add_edge(57, 23)
    graph.add_edge(2, 42)

    graph.write_nodes()
    graph.write_edges()
    with pytest.raises(Exception):
        graph.write_nodes(fail_if_exists=True)
    with pytest.raises(Exception):
        graph.write_edges(fail_if_exists=True)


def test_graph_fail_if_not_exists(provider_factory):
    graph_provider = provider_factory("w")
    graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(42, 23)
    graph.add_edge(57, 23)
    graph.add_edge(2, 42)

    with pytest.raises(Exception):
        graph.write_nodes(fail_if_not_exists=True)
    with pytest.raises(Exception):
        graph.write_edges(fail_if_not_exists=True)


def test_graph_write_attributes(provider_factory):
    graph_provider = provider_factory("w")
    graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(42, 23)
    graph.add_edge(57, 23)
    graph.add_edge(2, 42)

    graph.write_nodes(attributes=["position", "swip"])
    graph.write_edges()

    graph_provider = provider_factory("r")
    compare_graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    nodes = []
    for node, data in graph.nodes(data=True):
        if node == 2:
            continue
        if "zap" in data:
            del data["zap"]
        data["position"] = list(data["position"])
        nodes.append((node, data))

    compare_nodes = compare_graph.nodes(data=True)
    compare_nodes = [
        (node_id, data) for node_id, data in compare_nodes if len(data) > 0
    ]
    assert nodes == compare_nodes


def test_graph_write_roi(provider_factory):
    graph_provider = provider_factory("w")
    graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(42, 23)
    graph.add_edge(57, 23)
    graph.add_edge(2, 42)

    write_roi = Roi((0, 0, 0), (6, 6, 6))
    graph.write_nodes(roi=write_roi)
    graph.write_edges(roi=write_roi)

    graph_provider = provider_factory("r")
    compare_graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    nodes = sorted(list(graph.nodes()))
    nodes.remove(2)  # node 2 has no position and will not be queried
    nodes.remove(57)  # node 57 is outside of the write_roi
    compare_nodes = compare_graph.nodes(data=True)
    compare_nodes = [node_id for node_id, data in compare_nodes if len(data) > 0]
    compare_nodes = sorted(list(compare_nodes))
    edges = sorted(list(graph.edges()))
    edges.remove((2, 42))  # node 2 has no position and will not be queried
    compare_edges = sorted(list(compare_graph.edges()))

    assert nodes == compare_nodes
    assert edges == compare_edges


def test_graph_connected_components(provider_factory):
    graph_provider = provider_factory("w")
    graph = graph_provider[Roi((0, 0, 0), (10, 10, 10))]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(57, 23)
    graph.add_edge(2, 42)

    components = graph.get_connected_components()
    assert len(components) == 2
    c1, c2 = components
    n1 = sorted(list(c1.nodes()))
    n2 = sorted(list(c2.nodes()))

    compare_n1 = [2, 42]
    compare_n2 = [23, 57]

    if 2 in n2:
        temp = n2
        n2 = n1
        n1 = temp

    assert n1 == compare_n1
    assert n2 == compare_n2


def test_graph_has_edge(provider_factory):
    graph_provider = provider_factory("w")

    roi = Roi((0, 0, 0), (10, 10, 10))
    graph = graph_provider[roi]

    graph.add_node(2, comment="without position")
    graph.add_node(42, position=(1, 1, 1))
    graph.add_node(23, position=(5, 5, 5), swip="swap")
    graph.add_node(57, position=Coordinate((7, 7, 7)), zap="zip")
    graph.add_edge(42, 23)
    graph.add_edge(57, 23)

    write_roi = Roi((0, 0, 0), (6, 6, 6))
    graph.write_nodes(roi=write_roi)
    graph.write_edges(roi=write_roi)

    assert graph_provider.has_edges(roi)
