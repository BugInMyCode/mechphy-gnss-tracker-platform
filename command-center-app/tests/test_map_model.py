from __future__ import annotations

import pytest

from mechphy_command_center.map_model import MapNode, map_node_from_row, project_nodes


def test_project_nodes_returns_empty_projection_for_no_nodes() -> None:
    projection = project_nodes([], width=500, height=300)

    assert projection.nodes == ()
    assert projection.width == 500
    assert projection.height == 300


def test_project_single_node_to_center() -> None:
    node = MapNode(node_id=4660, latitude=12.971599, longitude=77.594566, last_seen="now")

    projection = project_nodes([node], width=500, height=300)

    assert len(projection.nodes) == 1
    assert projection.nodes[0].x == pytest.approx(250.0)
    assert projection.nodes[0].y == pytest.approx(150.0)
    assert projection.nodes[0].node == node


def test_project_multiple_nodes_with_padding() -> None:
    southwest = MapNode(node_id=1, latitude=10.0, longitude=70.0, last_seen="a")
    northeast = MapNode(node_id=2, latitude=20.0, longitude=80.0, last_seen="b")

    projection = project_nodes([southwest, northeast], width=500, height=300, padding=50)

    assert projection.nodes[0].x == pytest.approx(50.0)
    assert projection.nodes[0].y == pytest.approx(250.0)
    assert projection.nodes[1].x == pytest.approx(450.0)
    assert projection.nodes[1].y == pytest.approx(50.0)


def test_map_node_from_row() -> None:
    row = {
        "node_id": "4660",
        "latitude_degrees": "12.971599",
        "longitude_degrees": "77.594566",
        "last_seen": "2026-06-25T00:00:00Z",
    }

    node = map_node_from_row(row)

    assert node.node_id == 4660
    assert node.latitude == pytest.approx(12.971599)
    assert node.longitude == pytest.approx(77.594566)
    assert node.last_seen == "2026-06-25T00:00:00Z"


def test_project_nodes_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="width and height"):
        project_nodes([MapNode(1, 0.0, 0.0, "now")], width=0, height=300)
