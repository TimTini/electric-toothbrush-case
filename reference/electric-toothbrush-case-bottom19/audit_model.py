"""Independent geometry checks for the exported parametric toothbrush case."""
from pathlib import Path
import argparse
import json
import math
import numpy as np
import trimesh
import manifold3d as md

PROJECT=Path(__file__).resolve().parents[2]
EXPORTS=PROJECT/"exports/ban-day-du"

parser = argparse.ArgumentParser()
parser.add_argument('--body', type=Path, default=EXPORTS/'body.stl')
parser.add_argument('--cap', type=Path, default=EXPORTS/'cap.stl')
args = parser.parse_args()
collapsed_faces={}

def load(path):
    mesh = trimesh.load_mesh(path, process=True)
    # Float32 STL can collapse tiny boolean intersection triangles to a line.
    # Discard only repeated-index faces; this cannot fill a hole or alter volume.
    f=mesh.faces
    keep=(f[:,0]!=f[:,1]) & (f[:,1]!=f[:,2]) & (f[:,0]!=f[:,2])
    collapsed_faces[path.name]=int((~keep).sum())
    mesh.update_faces(keep)
    assert mesh.is_watertight and mesh.is_winding_consistent, str(path)
    solid = md.Manifold(md.Mesh(vert_properties=np.asarray(mesh.vertices,dtype=np.float32),
                              tri_verts=np.asarray(mesh.faces,dtype=np.uint32)))
    assert solid.status() == md.Error.NoError and len(solid.decompose()) == 1
    return mesh, solid

body_mesh, body = load(args.body)
cap_mesh, cap = load(args.cap)
assert body.genus() == 19 and cap.genus() == 0
for mesh, height in [(body_mesh,213.6),(cap_mesh,85.2)]:
    assert abs(mesh.bounds[0,2]) < .0001
    assert abs(mesh.bounds[1,2]-height) < .0001
    assert np.allclose(mesh.extents[:2],[51.4,51.4],atol=.005), mesh.extents

# Measure the restored outer R3.6 arc independently on both exported parts.
for solid in (body, cap):
    for z in (0.5, 1., 2., 3.6):
        expected_r = 25.7-3.6+math.sqrt(3.6**2-(z-3.6)**2)
        for angle in (0,45,120,270):
            a=math.radians(angle)
            hits=solid.ray_cast([0,0,z],[30*math.cos(a),30*math.sin(a),z])
            # Allow radial error from the 16-segment quarter-circle tessellation.
            assert hits and abs(30*hits[-1].distance-expected_r)<.012, (z,angle,hits)

# Sample cross-sections: a minimal cylinder has vertices only at its end rings.
for solid, inside in [(body,21.2),(cap,24)]:
    for z in [10,25,50]:
        for angle in [0,45,120,270]:
            a=math.radians(angle)
            hits=solid.ray_cast([0,0,z],[30*math.cos(a),30*math.sin(a),z])
            radii=[30*h.distance for h in hits]
            assert len(radii)==2 and np.allclose(radii,[inside,25.7],atol=.004),radii
for angle in [0,30,45,90,180,270]:
    a=math.radians(angle)
    hits=body.ray_cast([0,0,201.5],[30*math.cos(a),30*math.sin(a),201.5])
    assert abs(30*hits[0].distance-21.2)<.004

# All former side-drain axes are sealed. Sample 32 angles, including old bores.
for i in range(32):
    angle=2*math.pi*i/32
    radial=np.array([math.cos(angle),math.sin(angle),0.])
    assert len(body.ray_cast((26.4*radial+[0,0,-2]).tolist(),
                            (18.4*radial+[0,0,6]).tolist()))==2
centers=[(0.,0.)]
for radius,count,phase in [(7,6,0),(14,12,15)]:
    for i in range(count):
        a=math.radians(phase+i*360/count)
        centers.append((radius*math.cos(a),radius*math.sin(a)))
assert len(centers)==19
for x,y in centers:
    assert len(body.ray_cast([x,y,-1],[x,y,3]))==0
    for offset,expected in [(1.45,0),(1.55,2)]:
        assert len(body.ray_cast([x+offset,y,-1],[x+offset,y,3]))==expected
bottom_web=min(math.dist(a,b)-3 for i,a in enumerate(centers) for b in centers[i+1:])
assert bottom_web>=3.99,bottom_web
for i,a in enumerate(centers):
    for b in centers[i+1:]:
        if math.dist(a,b)<8:
            x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
            assert len(body.ray_cast([x,y,-1],[x,y,3]))==2

# Compare against independently exported no-drain and OFF variants.
checks=EXPORTS/'checks'
no_drains_mesh,no_drains=load(checks/'body-no-drains.stl')
assert no_drains.genus()==0 and no_drains_mesh.volume>body_mesh.volume
wide_cap_mesh,wide_cap=load(checks/'cap-clearance-04.stl')
assert wide_cap.genus()==0 and wide_cap_mesh.volume<cap_mesh.volume
hits=wide_cap.ray_cast([0,0,30],[30,0,30])
assert np.allclose([30*h.distance for h in hits],[24.2,25.7],atol=.004)
for name,mesh,solid in [('body',body_mesh,body),('cap',cap_mesh,cap)]:
    off_mesh,off_solid=load(checks/f'{name}.off')
    assert np.allclose(off_mesh.bounds,mesh.bounds,atol=.0001)
    assert off_solid.genus()==solid.genus()
    # OFF uses six significant digits: at Z>200 mm rounding reaches 0.0005 mm.
    # Allow ten ppm in volume; bounds and topology are checked separately above.
    assert np.isclose(off_mesh.volume,mesh.volume,rtol=1e-5,atol=.001)

# Independently subtract the intended nineteen cylinders and compare full volume.
bores=[md.Manifold.cylinder(2.64,1.5,circular_segments=48).translate([x,y,-.02])
       for x,y in centers]
expected_body=no_drains-md.Manifold.batch_boolean(bores,md.OpType.Add)
assert expected_body.genus()==19
sym_difference=abs((expected_body-body).volume())+abs((body-expected_body).volume())
assert sym_difference<.01,sym_difference
removed=no_drains^md.Manifold.batch_boolean(bores,md.OpType.Add)
assert len(removed.decompose())==19
assert np.allclose([removed.bounding_box()[2],removed.bounding_box()[5]],[0,2.6],atol=.0001)
expected_removed_volume=19*2.6*48/2*1.5**2*math.sin(2*math.pi/48)
assert abs((no_drains.volume()-body.volume())-expected_removed_volume)<.01

# Target dimensions define the assembly transform, independently of SCAD.
pitch = 4.68
seat = 200+85.2
rotation = ((seat-(71.2-pitch*90/360)-(202.45+pitch/2))/pitch*360)%360
collision_volumes=[]
for angle in [0,45,90,180,270,360,540,720,900,1080]:
    assembled_cap = cap.rotate([180,0,0]).rotate([0,0,rotation+angle]).translate([0,0,seat+pitch*angle/360])
    overlap = body ^ assembled_cap
    volume = abs(overlap.volume())
    assert volume < .0001, ('Thread interference',angle,volume)
    collision_volumes.append(volume)
closed_cap=cap.rotate([180,0,0]).rotate([0,0,rotation]).translate([0,0,seat])
usable_height=seat-2*2.6
assert abs(usable_height-280)<.0001
fit_proxy=md.Manifold.cylinder(270,17.5,circular_segments=240).translate([0,0,7.6])
proxy_collisions=[abs((part^fit_proxy).volume()) for part in [body,closed_cap]]
assert max(proxy_collisions)<.0001,proxy_collisions
# A 35 mm head can pass the entire body opening; sweep it as a tall cylinder.
insertion_proxy=md.Manifold.cylinder(300,17.5,circular_segments=240).translate([0,0,7.6])
assert abs((body^insertion_proxy).volume())<.0001
report = dict(body_faces=len(body_mesh.faces),cap_faces=len(cap_mesh.faces),
              body_bounds=body_mesh.bounds.tolist(),cap_bounds=cap_mesh.bounds.tolist(),
              body_genus=body.genus(),cap_genus=cap.genus(),
              outside_bottom_radius_mm=3.6,outer_bottom_arc_sampled=True,
              body_volume_mm3=body.volume(),cap_volume_mm3=cap.volume(),
              assembly_height_mm=seat,assembly_cap_rotation_degrees=rotation,
              screw_motion_collision_volumes_mm3=collision_volumes,
              side_drains_disabled=True,side_wall_axes_sealed=32,
              bottom_holes_open=19,bottom_hole_diameter_mm=3,
              bottom_layers=[dict(radius_mm=0,count=1),dict(radius_mm=7,count=6),
                             dict(radius_mm=14,count=12,phase_degrees=15)],
              bottom_hole_minimum_web_mm=bottom_web,
              bottom_holes_to_inner_fillet_mm=2.9,
              independent_cut_symmetric_difference_mm3=sym_difference,
              removed_bounds=removed.bounding_box(),
              off_bounds_topology_volume_match=True,
              no_drain_variant_genus=no_drains.genus(),
              wider_clearance_variant_inner_radius_mm=30*hits[0].distance,
              nominal_body_throat_diameter_mm=42.4,body_inside_diameter_mm=42.4,
              body_wall_thickness_mm=4.5,neck_wall_thickness_mm=1.8,usable_axial_length_mm=usable_height,
              reference_proxy_diameter_mm=35,reference_proxy_length_mm=270,
              reference_proxy_collision_volumes_mm3=proxy_collisions,
              reference_proxy_axial_margin_each_end_mm=5,
              reference_proxy_passes_body_mouth=True,
              repeated_index_zero_area_faces=collapsed_faces)
(EXPORTS/'audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
