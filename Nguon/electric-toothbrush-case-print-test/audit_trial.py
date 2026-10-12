"""Check the short trial against the verified full-size bottom19 STL."""
from pathlib import Path
import json
import math
import numpy as np
import trimesh
import manifold3d as md

ROOT=Path(__file__).parent
PROJECT=ROOT.parents[1]
EXPORTS=PROJECT/'exports/in-thu'
FULL=PROJECT/'exports/ban-day-du'


def load(path, components=1):
    mesh=trimesh.load_mesh(path,process=True)
    assert mesh.is_watertight and mesh.is_winding_consistent,path
    assert len(mesh.split())==components,path
    f=mesh.faces
    assert np.all((f[:,0]!=f[:,1]) & (f[:,1]!=f[:,2]) & (f[:,0]!=f[:,2]))
    solid=md.Manifold(md.Mesh(vert_properties=np.asarray(mesh.vertices,dtype=np.float32),
                             tri_verts=np.asarray(f,dtype=np.uint32)))
    assert solid.status()==md.Error.NoError
    return mesh,solid


def crop(solid,low,high):
    box=md.Manifold.cube([60,60,high-low]).translate([-30,-30,low])
    return solid^box


def difference(a,b):
    return abs((a-b).volume())+abs((b-a).volume())


body_mesh,body=load(EXPORTS/'body.stl')
cap_mesh,cap=load(EXPORTS/'cap.stl')
layout_mesh,_=load(EXPORTS/'layout.stl',2)
full_body_mesh,full_body=load(FULL/'body.stl')
full_cap_mesh,full_cap=load(FULL/'cap.stl')
assert body.genus()==19 and cap.genus()==0
for mesh,height in [(body_mesh,31.6),(cap_mesh,24)]:
    assert np.allclose(mesh.bounds[0],[-25.7,-25.7,0],atol=.0001)
    assert np.allclose(mesh.bounds[1],[25.7,25.7,height],atol=.0001)

# Full-size bottom and entire neck/thread are unchanged up to axial translation.
comparisons={
    'body_bottom':difference(crop(body,0,10),crop(full_body,0,10)),
    'body_neck_and_thread':difference(crop(body,12,32),crop(full_body,194,214).translate([0,0,-182])),
    'cap_bottom':difference(crop(cap,0,7),crop(full_cap,0,7)),
    'cap_thread_and_lip':difference(crop(cap,8,25),crop(full_cap,69.2,86.2).translate([0,0,-61.2]))}
assert max(comparisons.values())<.01,comparisons
centers=[(0.,0.)]
for radius,count,phase in [(7,6,0),(14,12,15)]:
    for i in range(count):
        a=math.radians(phase+360*i/count)
        centers.append((radius*math.cos(a),radius*math.sin(a)))
for x,y in centers:
    assert len(body.ray_cast([x,y,-1],[x,y,3]))==0
    assert len(body.ray_cast([x+1.45,y,-1],[x+1.45,y,3]))==0
    assert len(body.ray_cast([x+1.55,y,-1],[x+1.55,y,3]))==2
pitch=4.68
seat=42
rotation=((seat-(10-pitch*90/360)-(20.45+pitch/2))/pitch*360)%360
collisions=[]
for angle in [0,45,90,180,270,360,540,720,900,1080]:
    closed=cap.rotate([180,0,0]).rotate([0,0,rotation+angle]).translate([0,0,seat+pitch*angle/360])
    volume=abs((body^closed).volume())
    assert volume<.0001,(angle,volume)
    collisions.append(volume)
short_volume=body.volume()+cap.volume()
full_volume=full_body.volume()+full_cap.volume()
report=dict(body_height_mm=31.6,cap_height_mm=24,assembled_height_mm=42,
            outside_diameter_mm=51.4,body_inside_diameter_mm=42.4,body_wall_thickness_mm=4.5,bottom_holes=19,hole_diameter_mm=3,
            reference_region_symmetric_difference_mm3=comparisons,
            sampled_thread_collision_mm3=collisions,
            model_volume_mm3=short_volume,full_model_volume_mm3=full_volume,
            geometric_volume_reduction_percent=100*(1-short_volume/full_volume),
            physical_print_tested=False)
EXPORTS.joinpath('audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
