const K={"P": [108.337, 0.0, 49.0], "PIN": [108.337, 0.0, 99.0], "CRANK": [153.337, -45.617460457313626, 99.0], "r": 12.0, "L": 38.0, "e": 45.0, "t0": 70.0, "tout": 130.71447813974495, "s0": 21.617460457313623};

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
