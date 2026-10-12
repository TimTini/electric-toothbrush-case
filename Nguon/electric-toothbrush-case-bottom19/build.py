"""Export the standalone SCAD with the local OpenSCAD nightly (Python stdlib)."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess

ROOT=Path(__file__).parent
PROJECT=ROOT.parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--openscad',default=os.environ.get('OPENSCAD_EXECUTABLE',
    'openscad.com' if os.name == 'nt' else 'openscad'))
parser.add_argument('--previews',action='store_true')
parser.add_argument('--check-variants',action='store_true')
args=parser.parse_args()
exe=Path(shutil.which(args.openscad) or args.openscad).resolve()
if not exe.is_file():
    parser.error('Pass --openscad with the path to openscad.com, or set OPENSCAD_EXECUTABLE')
exports=PROJECT/'exports/ban-day-du'
exports.mkdir(parents=True,exist_ok=True)
source=PROJECT/'hop-ban-chai-dien.scad'
base=[str(exe),'--backend','Manifold','--hardwarnings','--check-parameters=true']
for part in ['body','cap','layout']:
    subprocess.run(base+['-D',f'output_part="{part}"','--export-format','binstl',
                         '-o',str(exports/f'{part}.stl'),str(source)],check=True)
if args.check_variants:
    checks=exports/'checks'
    checks.mkdir(exist_ok=True)
    for name,settings in [
        ('body.off',['output_part="body"']),
        ('cap.off',['output_part="cap"']),
        ('body-no-drains.stl',['output_part="body"','bottom_drains_enabled=false']),
        ('cap-clearance-04.stl',['output_part="cap"','thread_clearance=0.4'])]:
        defines=[arg for setting in settings for arg in ['-D',setting]]
        fmt=['--export-format','binstl'] if name.endswith('.stl') else []
        subprocess.run(base+defines+fmt+['-o',str(checks/name),str(source)],check=True)
if args.previews:
    for part in ['layout','bottom_detail','section','bottom_top']:
        view=['--camera','0,0,4,0,0,0,90','--projection','o'] if part=='bottom_top' else []
        model_part='bottom_detail' if part=='bottom_top' else part
        subprocess.run(base+['--render','--autocenter','--viewall','--imgsize','1100,1000',
                             '--colorscheme','Tomorrow','-D',f'output_part="{model_part}"']+view+[
                             '-o',str(exports/f'{part}.png'),str(source)],check=True)
