"""Convex hull helpers for sim-proxy geometry (scipy optional)."""

from __future__ import annotations

import hou


def _points_to_positions(points) -> list[tuple[float, float, float]]:
    return [(p.x(), p.y(), p.z()) for p in points]


def _create_aabb_hull(geo, points, flip_normals: bool = True) -> None:
    """Axis-aligned bounding box fallback when scipy/numpy are unavailable."""
    positions = _points_to_positions(points)
    if not positions:
        return

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    min_pt = (min(xs), min(ys), min(zs))
    max_pt = (max(xs), max(ys), max(zs))

    corners = [
        (min_pt[0], min_pt[1], min_pt[2]),
        (max_pt[0], min_pt[1], min_pt[2]),
        (max_pt[0], max_pt[1], min_pt[2]),
        (min_pt[0], max_pt[1], min_pt[2]),
        (min_pt[0], min_pt[1], max_pt[2]),
        (max_pt[0], min_pt[1], max_pt[2]),
        (max_pt[0], max_pt[1], max_pt[2]),
        (min_pt[0], max_pt[1], max_pt[2]),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]

    geo.clear()
    hull_points = [geo.createPoint() for _ in corners]
    for pt, pos in zip(hull_points, corners):
        pt.setPosition(pos)

    for face in faces:
        polygon = geo.createPolygon()
        indices = list(reversed(face)) if flip_normals else list(face)
        for idx in indices:
            polygon.addVertex(hull_points[idx])


def create_convex_hull(
    geo,
    points,
    normalize_parm=True,
    flip_normals_parm=True,
    simplify_parm=False,
    level_detail=0,
):
    """Create convex hull geometry; uses scipy when available, else AABB fallback."""
    try:
        import numpy as np
        import scipy.spatial as spatial
    except ImportError:
        _create_aabb_hull(geo, points, flip_normals=flip_normals_parm)
        return

    try:
        points_array = np.array([(p.x(), p.y(), p.z()) for p in points])

        if simplify_parm and level_detail > 0:
            grid_size = level_detail
            grid_points = np.round(points_array / grid_size) * grid_size
            hull_input = np.unique(grid_points, axis=0)
        else:
            hull_input = points_array

        if len(hull_input) < 4:
            _create_aabb_hull(geo, points, flip_normals=flip_normals_parm)
            return

        hull = spatial.ConvexHull(hull_input)

        hull_points_pos = hull_input[hull.vertices]
        centroid = np.mean(hull_points_pos, axis=0)
        centroid_vector = hou.Vector3(centroid[0], centroid[1], centroid[2])

        geo.clear()
        hull_points = []

        for point in range(len(hull.vertices)):
            pt = geo.createPoint()
            pos = hull_input[hull.vertices[point]]
            pt.setPosition((pos[0], pos[1], pos[2]))
            hull_points.append(pt)

        for face in hull.simplices:
            polygon = geo.createPolygon()
            face_points = []
            for id_ in face:
                vertex_id = np.where(hull.vertices == id_)[0][0]
                face_points.append(hull_points[vertex_id])

            if len(face_points) >= 3 and normalize_parm:
                v1 = face_points[1].position() - face_points[0].position()
                v2 = face_points[2].position() - face_points[0].position()
                normal = v1.cross(v2).normalized()
                center_to_face = face_points[0].position() - centroid_vector
                dot_product = normal.dot(center_to_face)
                should_reverse_face = dot_product < 0
                if flip_normals_parm:
                    should_reverse_face = not should_reverse_face
                if should_reverse_face:
                    face_points.reverse()

            for pt in face_points:
                polygon.addVertex(pt)

    except Exception as exc:
        hou.ui.displayMessage(
            f"Convex hull failed ({exc}); using bounding box fallback.",
            severity=hou.severityType.Warning,
        )
        _create_aabb_hull(geo, points, flip_normals=flip_normals_parm)
