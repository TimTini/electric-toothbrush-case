"""Math contracts; native Fusion execution is a separate check."""
import importlib.util
import math
import re
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('case_fusion', ROOT/'fusion/ElectricToothbrushCase/ElectricToothbrushCase.py')
case = importlib.util.module_from_spec(spec)
spec.loader.exec_module(case)

class RoundThreadTest(unittest.TestCase):
    def test_default_size_and_drains(self):
        p=case.defaults(); d=case.dimensions(p)
        self.assertEqual(p['outside_diameter'],51.4)
        self.assertEqual(p['outside_bottom_radius'],3.6)
        self.assertAlmostEqual(d['body_inner_r'],21.2)
        self.assertEqual(len(case.drain_centres(p)),19)
        case.validate(p); case.validate(case.defaults(True))

    def test_cap_has_scad_inward_ridge_not_cut_groove(self):
        p=case.defaults(); d=case.dimensions(p)
        cap=case.thread_geometry(p,True); body=case.thread_geometry(p,False)
        self.assertEqual((cap['operation'],body['operation']),('join','join'))
        self.assertAlmostEqual(cap['radius'],0.9)
        self.assertAlmostEqual(body['centre_r'],22.9)
        self.assertAlmostEqual(cap['centre_r'],24.1)
        self.assertAlmostEqual(cap['height'],11.7)
        self.assertAlmostEqual(cap['twist'],900)
        self.assertAlmostEqual(cap['phase'],90)
        self.assertAlmostEqual(cap['start'],71.2)
        self.assertAlmostEqual(d['cap_inner_r'],24)
        self.assertAlmostEqual(d['cap_wall'],1.7)

    def test_thread_nominals_match_both_scad_sources(self):
        for filename,short in (('hop-ban-chai-dien.scad',False),('in-thu.scad',True)):
            source=(ROOT/filename).read_text(encoding='utf-8')
            scalars={k:float(v) for k,v in re.findall(r'^([a-z_]+)\s*=\s*([0-9.]+);',source,re.M)}
            p=case.defaults(short); d=case.dimensions(p)
            for key in ('thread_pitch','thread_radius','thread_embed','thread_clearance','outside_bottom_radius','inside_bottom_radius'):
                self.assertAlmostEqual(p[key],scalars[key])
            self.assertRegex(source,r'(?m)^shoulder_height\s*=\s*body_height\s*-\s*neck_height\s*;')
            self.assertRegex(source,r'(?m)^body_thread_z\s*=\s*shoulder_height\s*\+\s*thread_offset\s*;')
            self.assertRegex(source,r'(?m)^cap_thread_z\s*=\s*cap_height\s*-\s*neck_height\s*-\s*cap_thread_offset\s*;')
            self.assertAlmostEqual(d['body_thread_z'],scalars['body_height']-scalars['neck_height']+scalars['thread_offset'])
            self.assertAlmostEqual(d['cap_thread_z'],scalars['cap_height']-scalars['neck_height']-scalars['cap_thread_offset'])
            self.assertAlmostEqual(d['cap_thread_turns'],scalars['cap_thread_turns'])
            self.assertAlmostEqual(p['cap_thread_phase'],scalars['cap_thread_phase'])

    def test_preserves_full_and_short_scad_dimensions(self):
        for short in (False, True):
            p=case.defaults(short); d=case.validate(p)
            self.assertAlmostEqual(d['body_inner_r'],21.2)
            self.assertAlmostEqual(d['neck_r'],23)
            self.assertAlmostEqual(d['body_shoulder_height'],18 if short else 200)
            self.assertAlmostEqual(d['body_thread_z'],20.45 if short else 202.45)
            self.assertAlmostEqual(d['cap_thread_z'],10 if short else 71.2)
            self.assertAlmostEqual(d['assembly_height'],42 if short else 285.2)

    def test_comments_are_vietnamese_for_every_parameter(self):
        self.assertTrue(set(case.BASE).issubset(case.COMMENTS))
        self.assertTrue(all(any(ord(c)>127 for c in text) for text in case.COMMENTS.values()))

    def test_ridges_interleave_half_pitch_after_cap_flipped(self):
        for changes in ({},{'body_height':31.6,'cap_height':24},{'outside_diameter':60},{'thread_turns':1.8},
                        {'cap_thread_phase':120,'cap_extra_turns':0.6,'cap_thread_offset':0.5}):
            p=dict(case.defaults(),**changes); d=case.validate(p)
            cap=case.thread_geometry(p,True); body=case.thread_geometry(p,False)
            phi=math.radians(d['assembly_rotation']); phase=math.radians(cap['phase'])
            for angle in (0,0.7,2,4,8):
                local=phi-phase-angle
                assembled_z=d['assembly_height']-cap['start']-p['thread_pitch']*local/(2*math.pi)
                body_z=body['start']+p['thread_pitch']*angle/(2*math.pi)
                self.assertAlmostEqual(assembled_z-body_z,p['thread_pitch']/2)

    def test_derived_formulas_match(self):
        for p in (case.defaults(),case.defaults(True),dict(case.defaults(),outside_diameter=60)):
            values=dict(p,PI=math.pi,floor=math.floor,max=max)
            for name,(expression,_) in case.DERIVED.items():
                values[name]=eval(expression.replace(';',',').replace(' deg',''),{'__builtins__':{}},values)
                self.assertAlmostEqual(values[name],case.dimensions(p)[name],places=8,msg=name)

    def test_assembled_ridges_have_clearance_over_full_body_thread(self):
        # Closest opposite helix point in the same/adjacent turns, including ends.
        for changes in ({},{'thread_pitch':4.5,'thread_radius':0.85,'thread_clearance':0.25},
                        {'cap_thread_phase':120,'cap_extra_turns':0.6,'cap_thread_offset':0.5}):
            p=dict(case.defaults(),**changes); d=case.validate(p)
            male=case.thread_geometry(p,False); female=case.thread_geometry(p,True)
            rotation=math.radians(d['assembly_rotation']); phase=math.radians(female['phase'])
            for i in range(101):
                a=math.radians(male['twist'])*i/100
                bx=male['centre_r']*math.cos(a);by=male['centre_r']*math.sin(a)
                bz=male['start']+p['thread_pitch']*a/(2*math.pi)
                minimum=float('inf')
                for j in range(2001):
                    v=math.radians(female['twist'])*j/2000
                    theta=rotation-phase-v
                    q=(female['centre_r']*math.cos(theta),female['centre_r']*math.sin(theta),
                       d['assembly_height']-female['start']-p['thread_pitch']*v/(2*math.pi))
                    minimum=min(minimum,math.dist((bx,by,bz),q))
                self.assertGreater(minimum-male['radius']-female['radius'],p['thread_clearance'])

    def test_tilted_end_planes_match_user_step(self):
        # mm; plane locations/normals measured from the user STEP exported 2026-10-11.
        references = (
            (True,False,(63.8696146012964,23.7710153042118,71.1854858858724),(-.341856910094204,.939692620785908,.0105655790827863)),
            (True,True,(63.8349630011408,-23.7952902013387,82.9134431566277),(.341856910094205,.939692620785908,.0105655790827858)),
            (False,False,(23.2289838816331,-.469589341812295,202.43472614253),(-.939692620785909,.341839368368375,.0111186633199148)),
            (False,True,(23.1198974225403,.313880076447322,211.820209259716),(.939692620785908,.341839368368375,.0111186633199144)))
        p=case.defaults()
        for cap,end,origin,normal in references:
            f=case.thread_end_frame(p,cap,end)
            pivot=tuple(v+(p['outside_diameter']+p['layout_gap'] if cap and i==0 else 0)
                        for i,v in enumerate(f['pivot']))
            self.assertAlmostEqual(abs(sum(a*b for a,b in zip(normal,f['normal']))),1,places=10)
            self.assertAlmostEqual(sum((a-b)*n for a,b,n in zip(pivot,origin,normal)),0,places=7)

    def test_end_axes_follow_short_size_phase_pitch_and_radius(self):
        p=case.defaults(True)
        q=dict(p,outside_diameter=60,cap_thread_phase=120,thread_turns=1.8,
               thread_pitch=4.5,thread_radius=.85,thread_end_tilt=60)
        for cap in (False,True):
            for end in (False,True):
                f=case.thread_end_frame(q,cap,end); t=case.thread_geometry(q,cap)
                self.assertAlmostEqual(f['centre'][2],t['start']+(t['height'] if end else 0))
                self.assertAlmostEqual(math.dist(f['centre'],f['pivot']),q['thread_radius']*
                    q[('cap' if cap else 'body')+('_end' if end else '_start')+'_pivot_fraction'])
                self.assertAlmostEqual(sum(a*b for a,b in zip(f['axis'],f['normal'])),0)
                self.assertAlmostEqual(sum(a*b for a,b in zip(f['tangent'],f['normal'])),.5)
                a,t=f['axis'],f['tangent']
                cross=(a[1]*t[2]-a[2]*t[1],a[2]*t[0]-a[0]*t[2],a[0]*t[1]-a[1]*t[0])
                for i in range(3):
                    self.assertAlmostEqual(t[i]*.5+cross[i]*math.sin(math.radians(60)),f['normal'][i])
        for changes in ({'thread_end_tilt':85},{'cap_end_pivot_fraction':1.2}):
            with self.assertRaises(ValueError): case.validate(dict(p,**changes))

    def test_diameter_changes_drains_and_both_mating_parts(self):
        p=dict(case.defaults(),outside_diameter=60); d=case.dimensions(p)
        self.assertAlmostEqual(d['body_inner_r'],25.5)
        self.assertAlmostEqual(d['neck_r'],27.3)
        self.assertGreater(len(case.drain_centres(p)),19)
        case.validate(p)

    def test_invalid_geometry_rejected(self):
        for changes in ({'neck_wall':1},{'thread_pitch':2},{'thread_turns':4},{'neck_height':10},{'bottom_drain_diameter':8},
                        {'wall_thickness':3}, {'cap_extra_turns':3}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                case.validate(dict(case.defaults(),**changes))

    def test_parameter_variants_keep_clearance_and_material(self):
        cases = ({'thread_pitch':4.5,'thread_radius':0.85,'thread_clearance':0.25},
                 {'bottom_drain_diameter':3.5}, {'thread_turns':1.8,'drain_outer_phase':20},
                 {'body_height':240,'cap_height':100}, {'outside_diameter':60})
        for changes in cases:
            with self.subTest(changes=changes):
                p=dict(case.defaults(),**changes); d=case.validate(p)
                self.assertGreaterEqual(d['cap_wall'],1.2)
                self.assertGreater(d['thread_start_gap'],0)
                self.assertGreater(d['thread_end_gap'],0)
                self.assertAlmostEqual(d['neck_inner_r'],d['body_inner_r'])
                centres=case.drain_centres(p)
                for i,a in enumerate(centres):
                    for b in centres[i+1:]:
                        self.assertGreaterEqual(math.dist(a,b)-p['bottom_drain_diameter'],3-1e-8)

if __name__=='__main__': unittest.main()
