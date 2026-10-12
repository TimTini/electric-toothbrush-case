"""Measure the exported body bore, including the shoulder and threaded neck."""
from pathlib import Path
import math
import numpy as np
import trimesh
import manifold3d as md

PROJECT = Path(__file__).resolve().parents[2]

for folder, height, shoulder in [('ban-day-du', 213.6, 200), ('in-thu', 31.6, 18)]:
    mesh = trimesh.load_mesh(PROJECT / 'exports' / folder / 'body.stl', process=True)
    assert mesh.is_watertight and mesh.is_winding_consistent
    solid = md.Manifold(md.Mesh(
        vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
        tri_verts=np.asarray(mesh.faces, dtype=np.uint32)))
    assert solid.status() == md.Error.NoError
    stations = np.linspace(5.5, height - .31, 80).tolist()
    stations += [shoulder - 4.4, shoulder - 1, shoulder, shoulder + .6, height - 1]
    for z in stations:
        for angle in [0, 30, 45, 90, 135, 180, 270]:
            a = math.radians(angle)
            hits = solid.ray_cast([0, 0, z], [30 * math.cos(a), 30 * math.sin(a), z])
            radius = 30 * hits[0].distance
            assert abs(radius - 21.2) < .004, (folder, z, angle, radius)
    # A full-bore gauge passes the entire straight wall and threaded mouth.
    gauge = md.Manifold.cylinder(height, 21.15, circular_segments=240).translate([0, 0, 5.5])
    assert abs((solid ^ gauge).volume()) < .0001, folder
    print(f'{folder}: bore diameter 42.4 mm at {len(stations)} stations; 42.3 mm gauge clears')
