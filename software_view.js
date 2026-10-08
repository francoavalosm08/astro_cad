/* Canvas 2D view for machines where WebGL is unavailable. */
window.createSoftwareViewer = function(plot, colors) {
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-label', 'Aircraft model software 3D view');
  plot.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  let last = null;
  let lastFaces = [];
  let lastHits = null, hitNames = [];
  let zoom = 1;
  let panX = 0, panY = 0;
  const colorCache=new Map();

  function unit(a) {
    const n = Math.hypot(...a) || 1;
    return a.map(x => x / n);
  }
  function cross(a, b) {
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  }
  function dot(a, b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
  function shade(hex, factor) {
    const key=hex+':'+factor.toFixed(2);
    if(colorCache.has(key))return colorCache.get(key);
    const rgb = [1,3,5].map(i => parseInt(hex.slice(i,i+2),16));
    const bytes=rgb.map(x => Math.max(0,Math.min(255,Math.round(x*factor))));
    const value={css:`rgb(${bytes.join(',')})`,bytes};
    colorCache.set(key,value);
    return value;
  }

  function drawRaster(faces,width,height){
    const image=ctx.createImageData(width,height),pixels=image.data;
    const depth=new Float32Array(width*height);depth.fill(-Infinity);
    const hits=new Int16Array(width*height);hits.fill(-1);
    for(let i=0;i<pixels.length;i+=4){pixels[i]=11;pixels[i+1]=21;pixels[i+2]=32;pixels[i+3]=255;}
    function paintFace(f,blend){
      const {x1,y1,x2,y2,x3,y3}=f;
      const d=(y2-y3)*(x1-x3)+(x3-x2)*(y1-y3);
      if(Math.abs(d)<1e-8)return;
      const inv=1/d;
      const xmin=Math.max(0,Math.floor(Math.min(x1,x2,x3)));
      const xmax=Math.min(width-1,Math.ceil(Math.max(x1,x2,x3)));
      const ymin=Math.max(0,Math.floor(Math.min(y1,y2,y3)));
      const ymax=Math.min(height-1,Math.ceil(Math.max(y1,y2,y3)));
      if(xmax<xmin||ymax<ymin)return;
      const ux=y2-y3,uy=x3-x2,vx=y3-y1,vy=x1-x3;
      const [r,g,b]=f.rgb;
      for(let y=ymin;y<=ymax;y++){
        const py=y+.5-y3,row=y*width;
        for(let x=xmin;x<=xmax;x++){
          const px=x+.5-x3;
          const u=(ux*px+uy*py)*inv;
          if(u<-.00001||u>1.00001)continue;
          const v=(vx*px+vy*py)*inv;
          if(v<-.00001||u+v>1.00001)continue;
          const z=u*f.z1+v*f.z2+(1-u-v)*f.z3;
          const n=row+x;
          if(z<=depth[n])continue;
          hits[n]=f.partId;
          const j=n*4;
          if(blend){
            const alpha=f.alpha,other=1-alpha;
            pixels[j]=pixels[j]*other+r*alpha;
            pixels[j+1]=pixels[j+1]*other+g*alpha;
            pixels[j+2]=pixels[j+2]*other+b*alpha;
          }else{
            depth[n]=z;
            pixels[j]=r;pixels[j+1]=g;pixels[j+2]=b;
          }
        }
      }
    }
    for(const f of faces)if(f.alpha===1)paintFace(f,false);
    for(const f of faces.filter(f=>f.alpha<1).sort((a,b)=>a.depth-b.depth))paintFace(f,true);
    ctx.putImageData(image,0,0);
    lastHits=hits;lastFaces=[];
  }

  function draw(parts, transformed, camera, transparent) {
    last = [parts, transformed, camera, transparent];
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(plot.clientWidth * ratio));
    const height = Math.max(1, Math.round(plot.clientHeight * ratio));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width; canvas.height = height;
    }
    ctx.fillStyle = '#0b1520'; ctx.fillRect(0,0,width,height);
    if (!parts.length) return;

    const eye = unit([camera.eye.x,camera.eye.y,camera.eye.z]);
    const right = unit(cross([camera.up.x,camera.up.y,camera.up.z],eye));
    const up = cross(eye,right);
    const objects = parts.map(p => ({p, vertices:transformed(p)}));
    const bounds = [Infinity,Infinity,Infinity,-Infinity,-Infinity,-Infinity];
    for (const {vertices} of objects) for (const v of vertices) {
      for (let k=0;k<3;k++) {
        bounds[k] = Math.min(bounds[k],v[k]);
        bounds[k+3] = Math.max(bounds[k+3],v[k]);
      }
    }
    const center = [0,1,2].map(k => (bounds[k]+bounds[k+3])/2);
    let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
    const projected = objects.map(({p,vertices}) => {
      const q = vertices.map(v => {
        const d=[v[0]-center[0],v[1]-center[1],v[2]-center[2]];
        const x=dot(d,right), y=dot(d,up), z=dot(d,eye);
        minX=Math.min(minX,x);maxX=Math.max(maxX,x);
        minY=Math.min(minY,y);maxY=Math.max(maxY,y);
        return [x,y,z];
      });
      return {p,q};
    });
    const scale=.88*zoom*Math.min(width/Math.max(1,maxX-minX),height/Math.max(1,maxY-minY));
    const midX=(minX+maxX)/2,midY=(minY+maxY)/2;
    const offsetX=panX*ratio,offsetY=panY*ratio;
    const faces=[];
    const names=[];
    for (const {p,q} of projected) {
      const partId=names.length;names.push(p.name);
      const color = p.group==='slot_roller'?'#ebd078':p.material==='PACF'?(p.motion==='fixed'?'#3291a5':'#ef8d40'):(colors[p.material]||'#aab7c0');
      const alpha = p.group==='wing'&&transparent?.23:p.material==='envelope'?.13:(transparent && (p.material==='LWPLA'||p.material==='PACF')?.42:1);
      for (const f of p.faces) {
        const a=q[f[0]],b=q[f[1]],c=q[f[2]];
        const x1=(a[0]-midX)*scale+width/2+offsetX,y1=height/2-(a[1]-midY)*scale+offsetY;
        const x2=(b[0]-midX)*scale+width/2+offsetX,y2=height/2-(b[1]-midY)*scale+offsetY;
        const x3=(c[0]-midX)*scale+width/2+offsetX,y3=height/2-(c[1]-midY)*scale+offsetY;
        const area=(x2-x1)*(y3-y1)-(x3-x1)*(y2-y1);
        if (Math.abs(area)<.01) continue;
        const normal=unit(cross([b[0]-a[0],b[1]-a[1],b[2]-a[2]],
                                [c[0]-a[0],c[1]-a[1],c[2]-a[2]]));
        const light=p.material==='LWPLA'?.93+.07*Math.abs(dot(normal,[.36,.48,.80]))
          :p.material==='PACF'?.35+.65*Math.max(0,dot(normal,[.36,.48,.80])):.78+.22*Math.abs(dot(normal,[.36,.48,.80]));
        const paint=shade(color,light);
        faces.push({x1,y1,x2,y2,x3,y3,z1:a[2],z2:b[2],z3:c[2],partId,name:p.name,
                    depth:(a[2]+b[2]+c[2])/3,fill:paint.css,rgb:paint.bytes,alpha});
      }
    }
    hitNames=names;
    if(ctx.createImageData && ctx.putImageData){
      drawRaster(faces,width,height);
    }else{
      lastHits=null;
      faces.sort((a,b)=>a.depth-b.depth);
      lastFaces=faces;
      let fill='',alpha=1;
      for (const f of faces) {
        if (f.fill!==fill) {ctx.fillStyle=f.fill;fill=f.fill;}
        if (f.alpha!==alpha) {ctx.globalAlpha=f.alpha;alpha=f.alpha;}
        ctx.beginPath();ctx.moveTo(f.x1,f.y1);ctx.lineTo(f.x2,f.y2);ctx.lineTo(f.x3,f.y3);
        ctx.closePath();ctx.fill();
      }
    }
    ctx.globalAlpha=1;
    const origin=[55*ratio,height-50*ratio];
    const axes=[['X',[1,0,0],'#ef8e79'],['Y',[0,1,0],'#8dd8ac'],['Z',[0,0,1],'#84baff']];
    ctx.font=`${12*ratio}px Arial,sans-serif`;
    ctx.lineWidth=2*ratio;
    for(const [label,axis,color] of axes){
      const vx=dot(axis,right)*29*ratio,vy=-dot(axis,up)*29*ratio;
      ctx.strokeStyle=color;ctx.fillStyle=color;
      ctx.beginPath();ctx.moveTo(origin[0],origin[1]);ctx.lineTo(origin[0]+vx,origin[1]+vy);ctx.stroke();
      ctx.fillText(label,origin[0]+vx+3*ratio,origin[1]+vy-3*ratio);
    }
  }
  canvas.addEventListener('wheel',event => {
    event.preventDefault();
    zoomBy(Math.exp(-event.deltaY*.001));
    if(last)draw(...last);
  },{passive:false});
  new ResizeObserver(() => { if (last) draw(...last); }).observe(plot);
  function zoomBy(factor){zoom=Math.max(.25,Math.min(8,zoom*factor));}
  function panBy(dx,dy){panX+=dx;panY+=dy;}
  function fit(){zoom=1;panX=0;panY=0;}
  function pick(clientX,clientY){
    const rect=canvas.getBoundingClientRect();
    const x=(clientX-rect.left)*canvas.width/rect.width;
    const y=(clientY-rect.top)*canvas.height/rect.height;
    if(lastHits){
      const ix=Math.floor(x),iy=Math.floor(y);
      if(ix<0||iy<0||ix>=canvas.width||iy>=canvas.height)return null;
      return hitNames[lastHits[iy*canvas.width+ix]]||null;
    }
    for(let i=lastFaces.length-1;i>=0;i--){
      const f=lastFaces[i];
      const d=(f.y2-f.y3)*(f.x1-f.x3)+(f.x3-f.x2)*(f.y1-f.y3);
      if(Math.abs(d)<1e-8)continue;
      const u=((f.y2-f.y3)*(x-f.x3)+(f.x3-f.x2)*(y-f.y3))/d;
      if(u<0||u>1)continue;
      const v=((f.y3-f.y1)*(x-f.x3)+(f.x1-f.x3)*(y-f.y3))/d;
      if(v>=0&&u+v<=1)return f.name;
    }
    return null;
  }
  return {draw,canvas,zoomBy,panBy,fit,pick};
};
