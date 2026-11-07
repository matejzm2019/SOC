// A local WebGL viewer of the actual Blender-exported meshes, units millimetres.
export function createHouseView(root) {
 const canvas=root.querySelector('canvas'),status=root.querySelector('[data-house-status]');
 const gl=canvas.getContext('webgl',{antialias:true});
 let meshes=[],groups={},selected=-1,roof=0,hideRoof=false,yaw=-.63,pitch=.78,zoom=2,focus=[300,225,115],drag=null,lastState=null;
 const set=(s,t)=>{const n=root.querySelector(s);if(n)n.textContent=t;};
 if(!gl){status.textContent='3D zobrazenie nie je dostupné. Použi obrázky a pôdorys v stavebných podkladoch.';return {update(){}};}
 const shader=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
 const program=gl.createProgram();
 gl.attachShader(program,shader(gl.VERTEX_SHADER,`attribute vec3 aP;attribute vec3 aN;uniform vec3 uFocus;uniform vec2 uAngles;uniform float uScale;uniform float uAspect;uniform float uLift;varying float light;void main(){vec3 p=aP+vec3(0.,0.,uLift)-uFocus;float c=cos(uAngles.x),s=sin(uAngles.x);vec3 q=vec3(c*p.x-s*p.y,s*p.x+c*p.y,p.z);float cp=cos(uAngles.y),sp=sin(uAngles.y);float yy=sp*q.y+cp*q.z;float zz=-cp*q.y+sp*q.z;gl_Position=vec4(q.x*uScale/uAspect,yy*uScale,-zz/2000.,1.);light=.55+.45*max(dot(normalize(aN),normalize(vec3(-.35,-.5,1.))),0.);}`));
 gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`precision mediump float;uniform vec3 uColor;varying float light;void main(){gl_FragColor=vec4(uColor*light,1.);}`));
 gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
 const loc={};for(const n of ['uFocus','uAngles','uScale','uAspect','uLift','uColor'])loc[n]=gl.getUniformLocation(program,n);
 const ap=gl.getAttribLocation(program,'aP'),an=gl.getAttribLocation(program,'aN');
 gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
 function draw(){
  const w=Math.max(1,canvas.clientWidth),h=Math.max(1,canvas.clientHeight),d=Math.min(devicePixelRatio||1,2);
  if(canvas.width!==Math.round(w*d)||canvas.height!==Math.round(h*d)){canvas.width=Math.round(w*d);canvas.height=Math.round(h*d);}
  gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.91,.93,.96,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  gl.uniform3fv(loc.uFocus,focus);gl.uniform2f(loc.uAngles,yaw,pitch);gl.uniform1f(loc.uScale,zoom/650);gl.uniform1f(loc.uAspect,w/h);
  for(const m of meshes){
   if(hideRoof && (m.g===1||m.g===2))continue;
   gl.bindBuffer(gl.ARRAY_BUFFER,m.pb);gl.vertexAttribPointer(ap,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(ap);
   gl.bindBuffer(gl.ARRAY_BUFFER,m.nb);gl.vertexAttribPointer(an,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(an);
   let color=m.c;
   const t=lastState&&!lastState.demo.enabled&&lastState.device.online?lastState.device.telemetry:null;
   if(m.g===12||m.g===13){const on=t?Boolean(t.load_stage&(m.g===12?1:2)):false;color=on?[1,.8,.25]:[.35,.3,.22];}
   if(m.g===17){const on=t&&t.grid_available;color=on?[.25,.6,1]:[.12,.2,.25];}
   if(m.g===selected)color=color.map((v,i)=>Math.min(1,v*.65+[.2,.3,.35][i]));
   gl.uniform3fv(loc.uColor,color);gl.uniform1f(loc.uLift,(m.g===1||m.g===2)?roof:0);gl.drawArrays(gl.TRIANGLES,0,m.count);
  }
 }
 function reset(){yaw=-.63;pitch=.78;zoom=2;focus=[300,225,115];selected=-1;roof=0;hideRoof=false;root.querySelector('[data-roof]').value='0';root.querySelector('[data-roof-hide]').checked=false;set('[data-roof-value]','0 mm');root.querySelector('select').value='-1';draw();}
 root.querySelector('[data-roof]').addEventListener('input',e=>{roof=Number(e.target.value);set('[data-roof-value]',`${roof} mm`);draw();});
 root.querySelector('[data-roof-hide]').addEventListener('change',e=>{hideRoof=e.target.checked;draw();});
 root.querySelector('[data-house-reset]').addEventListener('click',reset);
 root.querySelector('[data-house-top]').addEventListener('click',()=>{pitch=Math.PI/2;yaw=0;hideRoof=true;root.querySelector('[data-roof-hide]').checked=true;draw();});
 root.querySelector('select').addEventListener('change',e=>{selected=Number(e.target.value);if(selected<0){reset();return;}hideRoof=[3,4,5,6,7,8,9,12,13,15,16].includes(selected);root.querySelector('[data-roof-hide]').checked=hideRoof;if(!hideRoof){roof=0;root.querySelector('[data-roof]').value='0';set('[data-roof-value]','0 mm');}const points=meshes.filter(m=>m.g===selected).flatMap(m=>m.positions);const xs=[],ys=[],zs=[];for(let i=0;i<points.length;i+=3){xs.push(points[i]);ys.push(points[i+1]);zs.push(points[i+2]);}focus=[(Math.min(...xs)+Math.max(...xs))/2,(Math.min(...ys)+Math.max(...ys))/2,(Math.min(...zs)+Math.max(...zs))/2];zoom=(selected>=3&&selected<=10)||selected===16||selected===17?5:selected===14?4:2;draw();});
 canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
 canvas.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-drag[0])*.007;pitch=Math.max(.1,Math.min(1.57,pitch+(e.clientY-drag[1])*.006));drag=[e.clientX,e.clientY];draw();});
 canvas.addEventListener('pointerup',()=>{drag=null;});canvas.addEventListener('pointercancel',()=>{drag=null;});
 canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.5,Math.min(5,zoom*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
 canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','Home'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')yaw-=.1;if(e.key==='ArrowRight')yaw+=.1;if(e.key==='ArrowUp')pitch=Math.min(1.57,pitch+.1);if(e.key==='ArrowDown')pitch=Math.max(.1,pitch-.1);if(e.key==='+')zoom=Math.min(5,zoom*1.1);if(e.key==='-')zoom=Math.max(.5,zoom/1.1);if(e.key==='Home')reset();draw();});
 new ResizeObserver(draw).observe(canvas);
 fetch('/static/house/model.json').then(r=>{if(!r.ok)throw Error('Model sa nepodarilo načítať');return r.json();}).then(data=>{
  groups=data.groups;const select=root.querySelector('select');for(const [id,name] of Object.entries(groups)){const o=document.createElement('option');o.value=id;o.textContent=name;select.append(o);}
  meshes=data.meshes.map(m=>{const pb=gl.createBuffer(),nb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,pb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(m.p),gl.STATIC_DRAW);gl.bindBuffer(gl.ARRAY_BUFFER,nb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(m.n),gl.STATIC_DRAW);return {...m,positions:m.p,pb,nb,count:m.p.length/3};});
  status.textContent='Ťahanie: otáčanie · koliesko: priblíženie · šípky a +/−: klávesnica. Rozmery v mm.';draw();
 }).catch(e=>status.textContent=e.message);
 return {update(state){lastState=state;const t=!state.demo.enabled&&state.device.online?state.device.telemetry:null;set('[data-house-live]',t?`${t.telemetry_origin==='software_test'?'TESTOVACIE ÚDAJE':'ESP32 online'} · svetlá A ${t.load_stage&1?'zapnuté':'vypnuté'} · B ${t.load_stage&2?'zapnuté':'vypnuté'} · hlavný zdroj ${t.grid_available?'dostupný':'výpadok'}`:state.demo.enabled?'Softvérové demo: 3D model ukazuje konštrukciu; nejde o živé meranie svetiel.':'ESP32 offline: stav svetiel nie je známy.');draw();}};
}
