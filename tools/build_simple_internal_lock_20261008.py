"""Simplify the center lock to one servo, crank, rod and straight guided bolt."""
from pathlib import Path
import json,hashlib,shutil,copy
import numpy as np
import trimesh
from scipy.optimize import brentq
ROOT=Path('C:/Users/Box/OneDrive/Desktop/Astra V3')
SRC=Path('C:/Users/Box/AstraCADWork/20261008_internal_center_lock_mesh_preview')
OUT=Path('C:/Users/Box/AstraCADWork/20261008_simple_internal_slider_lock');OUT.mkdir(exist_ok=True)
source=json.loads((SRC/'model.js').read_text(encoding='utf8')[18:-1])
hashes={n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['model.js','context.js','pod-outer.js','mechanism.json']}
P=np.array([108.337,0.,49.]);PIN=P+[0,0,50.]
parts=[];meshes={}
def box(s,c):
 m=trimesh.creation.box(s);m.apply_translation(c);return m
def cyl(a,b,r):return trimesh.creation.cylinder(radius=r,segment=[a,b],sections=96)
def tube(a,b,ro,ri):return trimesh.boolean.difference([cyl(a,b,ro),cyl(np.array(a)-[0,1,0],np.array(b)+[0,1,0],ri)],engine='manifold')
def add(n,m,mat,motion='fixed',optional=False):
 assert m.is_volume,n
 meshes[n]=m;parts.append(dict(name=n,vertices=m.vertices.tolist(),faces=m.faces.tolist(),material=mat,motion=motion,group='lock_concept',optional_magnet=optional))
retained=[]
for q in source:
 if q['motion']=='rotating' or any(s in q['name'] for s in ['fixed_fork_cheek','CF_plate_mounted_lock_base','Lock_mount_M4','hard_stop','stop_support','bearing_support_spacer']):
  m=trimesh.Trimesh(q['vertices'],q['faces'],process=False);add(q['name'],m,q['material'],q['motion']);retained.append(q['name'])

# All bolt and rod centers lie at Z99: no rising pull arms or staged catch.
shaft=cyl(PIN+[0,-22,0],PIN+[0,11,0],3)
head=box([10,8,8],PIN+[0,-24,0])
bolt=trimesh.boolean.union([shaft,head],engine='manifold')
bolt=trimesh.boolean.difference([bolt,box([12,8,4],PIN+[0,-26,0]),cyl(PIN+[0,-24,-6],PIN+[0,-24,6],2.15)],engine='manifold')
add('Straight_6mm_locking_bolt_with_clevis',bolt,'steel','pin')
add('Straight_bolt_guide_sleeve',tube(PIN+[0,-18,0],PIN+[0,-9,0],5,3.1),'fixed')
add('Optional_magnet_seat_reference',tube(PIN+[0,-20,0],PIN+[0,-18,0],4,3.2),'magnet','fixed',True)
r,L,e=12.,38.,45.
def s(t):
 a=np.deg2rad(t);return r*np.cos(a)+np.sqrt(L*L-(e-r*np.sin(a))**2)
t0=70.;s0=s(t0);tout=brentq(lambda t:s0-s(t)-17,70,143)
CRANK=np.array([PIN[0]+e,-24-s0,PIN[2]])
def tip(t):
 a=np.deg2rad(t);return CRANK+[-r*np.sin(a),r*np.cos(a),0]
def st(t):return np.array([PIN[0],CRANK[1]+s(t),PIN[2]])
add('Release_servo_envelope_not_selected',box([32,16,30],CRANK+[0,0,-18]),'servo')
add('Servo_plate_mount_platform',box([40,20,3],CRANK+[0,0,-34.5]),'fixed')
for x in [-18,18]:add(f'Servo_plate_mount_post_{x}',box([4,16,40],np.array([CRANK[0]+x,CRANK[1],43])),'fixed')
add('Servo_output_shaft',cyl(CRANK+[0,0,-6],CRANK+[0,0,3],2.5),'steel')
add('12mm_servo_crank',cyl(CRANK,tip(t0),2),'servo','crank')
add('38mm_connecting_rod',cyl(tip(t0),st(t0),1.6),'link','rod')
add('Crank_rod_pivot',cyl(tip(t0)+[0,0,-3],tip(t0)+[0,0,3],2.1),'steel','crank')
add('Rod_bolt_clevis_pivot',cyl(st(t0)+[0,0,-4],st(t0)+[0,0,4],2.1),'steel','pin')
def rot(v,a,c=P):
 d=np.asarray(v)-c;t=np.deg2rad(a);w=d.copy();w[:,0]=np.cos(t)*d[:,0]-np.sin(t)*d[:,2];w[:,2]=np.sin(t)*d[:,0]+np.cos(t)*d[:,2];return w+c
def state(q,a=0,t=tout):
 m=meshes[q['name']].copy();v=m.vertices;pull=s0-s(t)
 if q['motion']=='rotating':m.vertices=rot(v,a)
 elif q['motion']=='pin':m.vertices=v+[0,-pull,0]
 elif q['motion']=='rod':m=cyl(tip(t),st(t),1.6)
 elif q['motion']=='crank':
  d=v-CRANK;z=np.deg2rad(t-t0);w=d.copy();w[:,0]=np.cos(z)*d[:,0]-np.sin(z)*d[:,1];w[:,1]=np.sin(z)*d[:,0]+np.cos(z)*d[:,1];m.vertices=w+CRANK
 return m
def ov(a,b):
 if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
 i=trimesh.boolean.intersection([a,b],engine='manifold');return float(i.volume) if len(i.faces) else 0.
fixed=trimesh.util.concatenate([state(q) for q in parts if q['motion']!='rotating' and 'mount_M4' not in q['name']])
moving=trimesh.util.concatenate([meshes[q['name']] for q in parts if q['motion']=='rotating'])
local=[]
for a in np.arange(0,90.01,.5):
 m=moving.copy();m.vertices=rot(m.vertices,a);v=ov(m,fixed)
 if v>.01:local.append([float(a),v])
structure=[(q,meshes[q['name']]) for q in parts if q['motion']=='fixed' and q['material']=='fixed']
release=[];rod_errors=[]
for t in np.linspace(t0,tout,61):
 rod_errors.append(abs(np.linalg.norm(tip(t)-st(t))-L))
 for q in parts:
  if q['motion'] not in ['rod','crank','pin']:continue
  m=state(q,t=t)
  for b,n in structure:
   v=ov(m,n)
   if v>.01:release.append([float(t),q['name'],b['name'],v])
inv_u=np.linspace(-1,1,20001);inv_x=inv_u*(227.5+12.5*np.tanh(4*inv_u)/np.tanh(4))
def implicit(v):
 d=np.asarray(v)-[P[0],0,3];u=np.interp(d[:,0],inv_x,inv_u)
 f=(d[:,1]/94)**2/np.maximum(1-u**6,1e-12)+(d[:,2]/125)**2/np.maximum(1-u*u,1e-12)
 return np.where((d[:,0]>inv_x[0])&(d[:,0]<inv_x[-1]),f,1e12)
outside=[]
for q in parts:
 for a,t in [(0,t0),(45,tout),(90,tout)]:
  m=state(q,a,t);maximum=float(implicit(m.vertices).max())
  if maximum>=1:outside.append([q['name'],a,maximum])
context=json.loads((SRC/'context.js').read_text(encoding='utf8')[21:-1])
battery=[(q,trimesh.Trimesh(q['vertices'],q['faces'],process=False)) for q in context if q['group']=='battery']
battery_hits=[]
for q in parts:
 if 'mount_M4' in q['name']:continue
 for a,t in [(0,t0),(45,tout),(90,tout)]:
  m=state(q,a,t)
  for b,n in battery:
   v=ov(m,n)
   if v>.01:battery_hits.append([q['name'],b['name'],a,v])
record=dict(preview_only=True,source=str(SRC),source_sha256=hashes,source_preserved=True,
 removed_parts=[q['name'] for q in source if q['name'] not in retained],retained_parts=retained,
 pivot_XYZ_mm=P.tolist(),pin_axis_point_XYZ_mm=PIN.tolist(),pin_axis='Y; straight axial translation',bolt_stroke_mm=17,
 rod_endpoint_Z_mm=99,crank_radius_mm=r,rod_length_mm=L,servo_offset_X_mm=e,crank_axis_XYZ_mm=CRANK.tolist(),servo_angles_deg=[t0,tout],
 circle_segments=96,local_motion_step_deg=.5,local_module_intersections=local,release_samples=61,release_structure_hits=release,
 max_rod_length_error_mm=max(rod_errors),outside_pod_samples=outside,battery_intersections=battery_hits,
 retention='Powered servo holding; optional axial ring magnet assist. No independent catch or spring return.',
 magnet_dimensions_reference_OD_ID_length_mm=[8,6.4,2],magnet_holding_force_unrated=True,magnet_default_enabled=False,
 full_aircraft_context_unchanged=True,plate_and_pod_mounting_unchanged=True,no_manufacturing_exports=True,
 qualification='Sampled mesh preview. Servo torque, magnetic retention, loss-of-power behavior and structural capacity not qualified. Full 35 mm tube/bearing/socket conversion remains deferred.')
(OUT/'checks.json').write_text(json.dumps(record,indent=2),encoding='utf8')
(OUT/'model.js').write_text('window.WING_PARTS='+json.dumps(parts,separators=(',',':'))+';',encoding='utf8')
for n in ['context.js','pod-outer.js','software_view.js']:shutil.copy2(SRC/n,OUT/n)
(OUT/'kinematics.json').write_text(json.dumps(dict(P=P.tolist(),PIN=PIN.tolist(),CRANK=CRANK.tolist(),r=r,L=L,e=e,t0=t0,tout=tout,s0=s0)),encoding='utf8')
meta=json.loads((SRC/'mechanism.json').read_text(encoding='utf8'));meta['simple_internal_slider_lock_revision']=record;(OUT/'mechanism.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
assert all(hashlib.sha256((SRC/n).read_bytes()).hexdigest()==h for n,h in hashes.items())
print(json.dumps(dict(local=local,release=release[:6],release_count=len(release),outside=outside,battery=battery_hits,servo_angles=[t0,tout],rod_error=max(rod_errors)),indent=2),flush=True)
