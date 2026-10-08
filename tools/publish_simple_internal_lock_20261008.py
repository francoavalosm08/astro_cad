from pathlib import Path
import json,re
ROOT=Path('C:/Users/Box/OneDrive/Desktop/Astra V3');SRC=Path('C:/Users/Box/AstraCADWork/20261008_internal_center_lock_mesh_preview');D=Path('C:/Users/Box/AstraCADWork/20261008_simple_internal_slider_lock')
k=json.loads((D/'kinematics.json').read_text());c=json.loads((D/'checks.json').read_text())
viewer='const K='+json.dumps(k)+';\n'+r'''
const E=id=>document.getElementById(id),parts=window.WING_PARTS;
const viewer=window.createSoftwareViewer(E('plot'),{carbon:'#273b45',composite:'#e0a04c',fixed:'#537e93',steel:'#c1c9cb',stop:'#dcc672',servo:'#8d7cb4',link:'#a9bec5',magnet:'#b18a58',battery:'#718b9c',insulator:'#e3e8eb',bearing:'#8298a3',tip:'#c2d9de',cf_plate:'#4d656d'});
let angle=0,retracted=false;
const views={iso:{eye:{x:1.7,y:-1.5,z:1.2},up:{x:0,y:0,z:1}},side:{eye:{x:0,y:-2,z:0},up:{x:0,y:0,z:1}},front:{eye:{x:2,y:0,z:0},up:{x:0,y:0,z:1}},top:{eye:{x:0,y:0,z:2},up:{x:1,y:0,z:0}}};let camera=views.iso;
function rot(v,a,c){a*=Math.PI/180;return v.map(q=>{let x=q[0]-c[0],z=q[2]-c[2];return[c[0]+Math.cos(a)*x-Math.sin(a)*z,q[1],c[2]+Math.sin(a)*x+Math.cos(a)*z];});}
function rz(v,a,c,out=c){let t=a*Math.PI/180;return v.map(q=>{let x=q[0]-c[0],y=q[1]-c[1];return[out[0]+Math.cos(t)*x-Math.sin(t)*y,out[1]+Math.sin(t)*x+Math.cos(t)*y,out[2]+q[2]-c[2]];});}
function s(t){t*=Math.PI/180;return K.r*Math.cos(t)+Math.sqrt(K.L*K.L-(K.e-K.r*Math.sin(t))**2);}
function tip(t){t*=Math.PI/180;return[K.CRANK[0]-K.r*Math.sin(t),K.CRANK[1]+K.r*Math.cos(t),K.CRANK[2]];}
function slider(t){return[K.PIN[0],K.CRANK[1]+s(t),K.PIN[2]];}
function transform(p){
 const t=retracted?K.tout:K.t0;
 if(p.motion==='rotating')return rot(p.vertices,angle,K.P);
 if(p.motion==='pin')return p.vertices.map(v=>[v[0],v[1]-(retracted?17:0),v[2]]);
 if(p.motion==='crank')return rz(p.vertices,t-K.t0,K.CRANK);
 if(p.motion==='rod'){
  let a=tip(K.t0),b=slider(K.t0),c=tip(t),d=slider(t),turn=(Math.atan2(d[1]-c[1],d[0]-c[0])-Math.atan2(b[1]-a[1],b[0]-a[0]))*180/Math.PI;
  return rz(p.vertices,turn,a,c);
 }
 return p.vertices;
}
function draw(){
 const hiddenCheek=camera.eye.y>=0?'far_fixed_fork_cheek_4mm':'near_fixed_fork_cheek_4mm';
 let selected=parts.filter(p=>(!p.optional_magnet||E('magnet').checked)&&(!E('cutaway').checked||p.name!==hiddenCheek));
 if(E('context').checked){
  let context=window.CONTEXT_PARTS.filter(p=>p.group==='battery'||p.group==='pod'||(E('aircraft').checked&&p.name!=='single_straight_rotating_CF_center_tube_8OD_6ID_reference'));
  if(E('podcut').checked)context=context.map(p=>p.group==='pod'?{...p,vertices:window.POD_OUTER.vertices,faces:window.POD_OUTER.faces.filter(f=>{
   if(Math.abs(camera.eye.y)<.01&&camera.eye.z>1.8)return f.reduce((sum,i)=>sum+window.POD_OUTER.vertices[i][2]-3,0)<0;
   return f.reduce((sum,i)=>sum+window.POD_OUTER.vertices[i][1],0)*(camera.eye.y>=0?1:-1)<0;
  })}:p);
  selected=selected.concat(context);
 }
 viewer.draw(selected,transform,camera,false);
 E('pitch').disabled=!retracted;E('pitch').value=angle;E('a').textContent=angle.toFixed(1)+'°';
 E('withdraw').disabled=retracted;E('engage').disabled=!retracted||!(angle===0||angle===90);
 E('cruise').disabled=E('hover').disabled=!retracted;
 E('state').textContent=retracted?'Bolt retracted 17 mm · frame may rotate':`Bolt engaged at ${angle}° · servo holds the slider${E('magnet').checked?' · magnet assist reference':''}`;
 E('stroke').textContent=`Servo crank ${(retracted?K.tout:K.t0).toFixed(1)}° · straight bolt travel ${retracted?'17.0':'0.0'} mm`;
}
E('withdraw').onclick=()=>{retracted=true;draw();};E('engage').onclick=()=>{if(angle===0||angle===90){retracted=false;draw();}};
for(const id of ['context','podcut','aircraft','cutaway','magnet'])E(id).onchange=()=>{viewer.fit();draw();};
E('cruise').onclick=()=>{angle=0;draw();};E('hover').onclick=()=>{angle=90;draw();};E('pitch').oninput=()=>{angle=Number(E('pitch').value);draw();};
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{camera=views[b.dataset.view];viewer.fit();draw();});E('fit').onclick=()=>{viewer.fit();draw();};E('plus').onclick=()=>{viewer.zoomBy(1.25);draw();};E('minus').onclick=()=>{viewer.zoomBy(.8);draw();};
let drag;viewer.canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];viewer.canvas.setPointerCapture(e.pointerId);};viewer.canvas.onpointermove=e=>{if(!drag)return;const dx=e.clientX-drag[0],dy=e.clientY-drag[1];drag=[e.clientX,e.clientY];let v=camera.eye,r=Math.hypot(v.x,v.y,v.z),az=Math.atan2(v.y,v.x)+dx*.008,ev=Math.max(-1.5,Math.min(1.5,Math.asin(v.z/r)+dy*.008));camera={eye:{x:r*Math.cos(ev)*Math.cos(az),y:r*Math.cos(ev)*Math.sin(az),z:r*Math.sin(ev)},up:{x:0,y:0,z:1}};draw();};viewer.canvas.onpointerup=()=>drag=null;draw();
'''
(D/'viewer.js').write_text(viewer,encoding='utf8')
h=(SRC/'index.html').read_text(encoding='utf8')
h=h.replace('Astra internal center lock','Astra simple internal slider-crank lock').replace('Center spar lock · inside the egg','Simple slider-crank · inside the egg')
h=h.replace('Lock and release servo mounted on the top battery CF plate, at the middle of the rotating spar. One retained pin locks 0° and 90°.','One servo crank, one connecting rod and one straight guided locking bolt. Mounted on the top CF battery plate, at the middle of the spar.')
h=h.replace('<button data-view="side">Side</button>','<button data-view="top">Top</button><button data-view="side">Side</button>')
h=h.replace('<div id="tools">','<div id="tools"><label><input id="magnet" type="checkbox">Magnet assist (optional)</label> ')
h=re.sub('<div class="legend">.*?</div>','<div class="legend">Orange: composite collar · Blue: fixed guide / frame · Gray: straight bolt and rod · Purple: servo and crank</div>',h)
h=re.sub('<button id="releaseCatch">.*?<button id="secure">.*?</button>','<button id="withdraw">Retract bolt</button><button id="engage">Engage bolt</button>',h)
h=h.replace('Packaging preview: battery stack lowered 18 mm; CF plate corners chamfered 20 mm. Egg outer contour and wing/motor positions retained. Plate mounts, catch cam, strength and full 35 mm bearing/socket conversion remain preliminary.','Servo holding requires power; optional magnet retention is unmeasured. No separate catch or return springs. Layout, loads, servo selection and the full 35 mm bearing/socket conversion remain preliminary.')
(D/'index.html').write_text(h,encoding='utf8')
report=f'''<!doctype html><html><head><meta charset="utf-8"><title>Simple internal slider-crank</title><style>body{{font:16px Arial;max-width:900px;margin:24px auto;padding:20px;color:#173443;background:#edf3f5}}p,li{{line-height:1.5}}td{{padding:10px;border-bottom:1px solid #bbd0d7}}table{{border-collapse:collapse;width:100%}}a{{color:#25647b}}</style></head><body><h1>Simple servo slider-crank</h1><p><a href="index.html">Designer</a> · <a href="checks.json">Checks</a></p><p>The red spring pull bars, both springs, green safety catch, catch pivot, cam shoe and their support arms are removed. The staged clevis and extra slider rails are replaced by one straight 6 mm locking bolt with a rear clevis and one guide sleeve. The two ordinary linkage pivots remain: one at the servo horn and one at the bolt clevis. They rotate about Z; the bolt translates along Y without changing its angle.</p>
<p>The rod and locking-bolt centers both stay at Z = 99 mm. The rod swings horizontally in XY and has no upward slope. A 12 mm servo crank and 38 mm connecting rod produce 17 mm bolt travel, over {k['t0']:.2f}° to {k['tout']:.2f}° of servo crank rotation. The servo is offset 45 mm along X and its base feet remain on the top CF plate. Battery placement, CF plate corners, pod, wings, motors, shaft axis and landing gear are unchanged from the preceding internal preview.</p>
<p>The bolt still engages the existing bushed holes at 0° and 90°. Transverse wing torque goes through the bolt and supporting fork into the plate; the servo maintains the bolt's axial position. This is the powered holding option requested by the user, with no independent anti-withdrawal catch. Loss of power is no longer qualified as a retained lock. Unload the indexing bolt before withdrawing it.</p>
<p>The optional magnet toggle shows an 8 mm OD × 6.4 mm ID × 2 mm ring at the end of the guide, contacting the front of the seated steel bolt head. It is an axial retaining aid, not the part that carries shaft torque. Grade, pull force, steel type and vibration retention are not selected or tested. Actual magnetic pull depends on the contact gap and target material; <a href="https://www.kjmagnetics.com/blog/testing-magnet-strength">K&amp;J's test explanation</a> notes that its listed pull values use zero-gap contact to specified steel. No zero-power retention claim is made for this reference magnet.</p>
<p>The released rotating module clears the fixed mechanism in 0.5° mesh samples through 0–90°. The crank, rod and sliding bolt clear the fixed support structure at 61 release positions; computed rod-length error is {c['max_rod_length_error_mm']:.2g} mm. Circular meshes use 96 segments. Endpoint packaging samples fit the egg and clear the battery. These are sampled geometric checks, not continuous collision proof or strength validation. The unchanged outer airframe retains the preceding wing/pod sweep evidence.</p>
<p>Servo torque, holding current, magnet retention, pin/fork and composite strength, plate reinforcement, final fits and the full 35 mm bearing/socket conversion remain unqualified. No manufacturing exports were generated. The preceding internal preview is preserved.</p></body></html>'''
(D/'report.html').write_text(report,encoding='utf8')
pointer=dict(preview=str(D),source_preview=str(SRC),url='http://127.0.0.1:8922/index.html',preview_only=True,internal_center_lock=True,full_35mm_shaft_conversion_deferred=True)
for n in ['selected_center_lock_concept_20261008.json','selected_free_pivot_quad_20261006.json']:(ROOT/'output'/n).write_text(json.dumps(pointer,indent=2),encoding='utf8')
print('Simple lock designer ready')
