"""Pure-Python map projection helpers for the placeholder map panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class MapNode:
    node_id: int
    latitude: float
    longitude: float
    last_seen: str


@dataclass(frozen=True)
class ProjectedNode:
    node: MapNode
    x: float
    y: float


@dataclass(frozen=True)
class MapProjection:
    nodes: tuple[ProjectedNode, ...]
    width: float
    height: float


def map_node_from_row(row: Mapping[str, Any]) -> MapNode:
    return MapNode(
        node_id=int(row["node_id"]),
        latitude=float(row["latitude_degrees"]),
        longitude=float(row["longitude_degrees"]),
        last_seen=str(row["last_seen"]),
    )


def project_nodes(
    nodes: Iterable[MapNode],
    width: float,
    height: float,
    padding: float = 32.0,
) -> MapProjection:
    node_list = tuple(nodes)

    if width <= 0 or height <= 0:
        raise ValueError("map width and height must be positive")
    if padding < 0:
        raise ValueError("map padding must be non-negative")
    if not node_list:
        return MapProjection(nodes=(), width=width, height=height)

    min_latitude = min(node.latitude for node in node_list)
    max_latitude = max(node.latitude for node in node_list)
    min_longitude = min(node.longitude for node in node_list)
    max_longitude = max(node.longitude for node in node_list)

    latitude_span = max_latitude - min_latitude
    longitude_span = max_longitude - min_longitude
    inner_width = max(width - (2.0 * padding), 1.0)
    inner_height = max(height - (2.0 * padding), 1.0)

    projected: list[ProjectedNode] = []
    for node in node_list:
        if longitude_span == 0:
            x = width / 2.0
        else:
            x = padding + ((node.longitude - min_longitude) / longitude_span) * inner_width

        if latitude_span == 0:
            y = height / 2.0
        else:
            y = padding + ((max_latitude - node.latitude) / latitude_span) * inner_height

        projected.append(ProjectedNode(node=node, x=x, y=y))

    return MapProjection(nodes=tuple(projected), width=width, height=height)
