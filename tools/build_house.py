"""Dimensioned timber demonstration house, Blender 4.3+. Run from repository root."""
import bpy, math, json, csv
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'model-domu'
for folder in ('3d','nahlady'):(OUT/folder).mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
ANGLE=math.radians(35);RIDGE=128+165*math.tan(ANGLE);objects=[]
def material(name,c,metal=0,rough=.5,grain=False):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*(v**2.2 for v in c),1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if grain:
  n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=85;n.inputs['Detail'].default_value=2
  ramp=m.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v**2.2*.75 for v in c),1);ramp.color_ramp.elements[1].color=(*(min(1,v**2.2*1.18) for v in c),1);m.node_tree.links.new(n.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
 return m
wood=material('Dubova preglejka',(.70,.53,.34),grain=True);cedar=material('Cedrovy obklad',(.58,.36,.20),grain=True);ivory=material('Tepla biela fasada',(.89,.88,.82));dark=material('Antracitove profily',(.16,.19,.21),rough=.37);roofmat=material('Antracitova falcovana strecha',(.23,.27,.29),metal=.25,rough=.38);stone=material('Sedy sokel a podstava',(.48,.51,.50));silver=material('Hlinik',(.68,.72,.73),.75,.28);glass=material('Matny akrylat okien',(.49,.65,.69),.12,.24);blue=material('PCB modra',(.045,.26,.40));green=material('PCB zelena',(.08,.33,.23));black=material('Elektronika',(.055,.065,.075));gold=material('Mosadz a kontakty',(.78,.62,.27),.65,.3);light=material('Tepla LED',(.98,.78,.35));solar=material('Monokrystalicke clanky',(.07,.14,.23),.42,.23)
# Warm emission is for the presentation render; the app colours LEDs from live telemetry.
led=light.node_tree.nodes.get('Principled BSDF');led.inputs['Emission Color'].default_value=(1,.62,.18,1);led.inputs['Emission Strength'].default_value=.6

def finish(o,name,mat,g,bevel=0):
 o.name=name;o.data.materials.append(mat);o['group']=g;objects.append(o)
 if bevel:
  bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Opracovane hrany','BEVEL');m.width=bevel/1000;m.segments=2;bpy.ops.object.modifier_apply(modifier=m.name)
 return o

def box(name,x,y,z,w,d,h,mat=wood,g=0,bevel=.25):
 bpy.ops.mesh.primitive_cube_add(size=1,location=((x+w/2)/1000,(y+d/2)/1000,(z+h/2)/1000));o=bpy.context.object;o.dimensions=(w/1000,d/1000,h/1000);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,g,min(bevel,min(w,d,h)/4))

def prism(name,v,f,mat,g):
 me=bpy.data.meshes.new(name);me.from_pydata([[q/1000 for q in p] for p in v],[],f);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,name,mat,g)

def cut(o,x,y,z,w,d,h):
 c=box('temp',x,y,z,w,d,h,bevel=0);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Otvor','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);objects.remove(c);bpy.data.objects.remove(c,do_unlink=True)

def hole(o,x,y,z,r,depth,along_y=False):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r/1000,depth=depth/1000,location=(x/1000,y/1000,z/1000),rotation=(math.pi/2,0,0) if along_y else (0,0,0));c=bpy.context.object;bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Priechod','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)

def tube(name,points,mat=black,g=0,r=.8):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r/1000;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=tuple(q/1000 for q in v)+(1,)
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');return finish(bpy.context.object,name,mat,g)

def roofbox(name,x,t,z,w,d,h,mat=roofmat,g=1,side=-1):
 # x/t/z denote centre: t is distance down the slope, z distance above deck.
 o=box(name,-w/2,-d/2,-h/2,w,d,h,mat,g)
 o.rotation_euler.x=-side*ANGLE;o.location=(x/1000,(235+side*t*math.cos(ANGLE)+side*z*math.sin(ANGLE))/1000,(RIDGE-t*math.sin(ANGLE)+z*math.cos(ANGLE))/1000);return o
base=box('P01 Podstava 600x450x8',0,0,0,600,450,8,stone,bevel=0)
for x,y in [(360,85),(360,385),(56,36),(96,36),(500,370)]:hole(base,x,y,4,3,12)
hole(base,119,36,4,1.5,12)
for x,y in ((35,23),(125,23),(35,53),(125,53)):hole(base,x,y,4,1.6,12)
for x in (15,565):
 for y in (15,415):box('Nozicka 10 mm',x,y,-10,20,20,10,black)
# Narrow edge banding and a clean entrance path are optional surface finishes.
for x in (0,596):box('Obvodova hrana podstavy',x,0,0,4,450,8,dark)
for y in (0,446):box('Obvodova hrana podstavy',0,y,0,600,4,8,dark)
for y in (7,28,49):box('Vstupny naslap 62x18x2',323,y,8,62,18,2,ivory)
front=box('P02 Predna stena 480x120x6',60,70,8,480,6,120,ivory)
for x in (100,214,426):cut(front,x,69,48,64,8,48)
back=box('P03 Zadna stena 480x120x6',60,394,8,480,6,120,ivory);hole(back,500,397,33,4,10,True)
for x in (110,245):cut(back,x,393,48,56,8,48)
left=box('P04 Lava stena 318x120x6',60,76,8,6,318,120,ivory)
for y in (135,300):cut(left,59,y,48,8,56,48)
right=box('P05 Prava stena 318x120x6',534,76,8,6,318,120,ivory);cut(right,533,140,48,8,56,48)
# Five cedar courses, each 6 mm high, applied below the windows.
for z in (13,20,27,34,41):
 for y in (68.5,400):box('A01 Vodorovny obklad celo',60,y,z,480,1.5,6,cedar)
 for x in (58.5,540):box('A01 Vodorovny obklad bok',x,76,z,1.5,318,6,cedar)
for x in (59,535):
 for y in (68,395):box('A02 Rohova krycia lista',x,y,8,6,7,120,dark)
# Recessed acrylic is optional; detailed frames and sills remain visible in all exports.
def window(x,y,w=64,side='front'):
 z=48;h=48
 if side in ('front','back'):
  out=y-2 if side=='front' else y+6
  for xx in (x-3,x+w):box('A03 Zvisly ram okna',xx,out,z-3,3,2,h+6,dark)
  for zz in (z-3,z+h):box('A03 Vodorovny ram okna',x-3,out,zz,w+6,2,3,dark)
  box('A04 Parapet',x-5,out-2,z-5,w+10,7,2,wood)
  box('A03 Stredovy priecnik',x+w/2-1,out,z,2,2,h,dark)
  box('Volitelny difuzny akrylat',x,y+2,z,w,.7,h,glass)
 else:
  out=x-2 if side=='left' else x+6
  for yy in (y-3,y+w):box('A03 Zvisly ram bocneho okna',out,yy,z-3,2,3,h+6,dark)
  for zz in (z-3,z+h):box('A03 Vodorovny ram bocneho okna',out,y-3,zz,2,w+6,3,dark)
  box('A04 Bocny parapet',out-2,y-5,z-5,7,w+10,2,wood)
  box('A03 Stredovy priecnik bocny',out,y+w/2-1,z,2,2,h,dark)
  box('Volitelny difuzny akrylat',x+2,y,z,.7,w,h,glass)
for x in (100,214,426):window(x,70)
for x in (110,245):window(x,394,56,'back')
for y in (135,300):window(60,y,56,'left')
window(534,140,56,'right')
# Fixed door insert: no hinges or furniture to manufacture.
box('A05 Dvere pevna doska 40x82x2',334,66,8,40,2,82,dark)
for x in (330,374):box('A05 Zarubna',x,65.5,8,4,3,86,wood)
box('A05 Nadprazie',330,65.5,90,48,3,4,wood)
box('A05 Sklo dveri',340,65.5,47,13,.5,35,glass)
box('A05 Madlo dveri',366,63.5,42,1.5,2,13,silver)
box('A05 Prah',330,62,8,48,10,2,stone)
# Furniture-free rooms with scored timber floor and labelled service plate.
for x in range(76,535,20):box('Volitelna podlahova ryha',x,77,8.1,.35,316,.15,cedar,bevel=0)
box('P06 Pozdlzna priecka 318x100x6',370,76,8,6,318,100,ivory)
box('P07 Priecna priecka 304x100x6',66,235,8,304,6,100,ivory)
box('P08 Technicka priecka 158x100x6',376,250,8,158,6,100,ivory)
box('P09 Servisna doska 150x132x4',380,257,10,150,132,4)
# 504 x 230 mm roof planes: enough space for the real 230 x 195 mm module.
for side in (-1,1):
 roofbox('ROOF P10 rovina 504x230x4',300,115,2,504,230,4,roofmat,1,side)
 for x in range(61,550,42):roofbox('ROOF A06 falc 230x1x1',x,115,4.6,1,230,1,dark,1,side)
 roofbox('ROOF A07 hrebenac 504x12x1',300,6,5.2,504,12,1,dark,1,side)
 roofbox('ROOF A08 odkvapova lista 504x6x4',300,228,1,504,6,4,dark,1,side)
 for x in (49,551):roofbox('ROOF A09 stitova lista 230x6x4',x,115,2,6,230,4,wood,1,side)
for x in (60,536):
 v=[(x,70,128),(x,400,128),(x,235,RIDGE),(x+4,70,128),(x+4,400,128),(x+4,235,RIDGE)]
 prism('ROOF P11 stit 330x116x4',v,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],ivory,1)
for x in (68,522):box('ROOF L01 nosnik 316x10x10',x,77,118,10,316,10,wood,1)
for x in (68,522):
 for y in (85,350):box('ROOF L02 doraz 30x10x6',x,y,112,10,30,6,wood,1)
for t in (30,195):roofbox('ROOF L03 vystuha 440x10x10',300,t,-5,440,10,10,wood)
# Surface mount rails carry the panel; clips grip its metal frame, not the cells.
for t in (35,191):roofbox('SOLAR L04 montazna lista 250x8x6',300,t,7,250,8,6,dark,2)
roofbox('SOLAR Panel 230x195x17',300,113,18.5,230,195,17,silver,2)
roofbox('SOLAR Tmave pozadie clankov',300,113,27.1,220,185,.4,black,2)
for i in range(6):
 for j in range(9):
  x=300-107.5+i*36; t=113-90+j*20.25
  roofbox('SOLAR Monokrystalicka bunka',x+17.25,t+9.5,27.4,34.5,19,.35,solar,2)
  roofbox('SOLAR Zbernica clanku',x+17.25,t+9.5,27.65,.45,18,.15,silver,2)
for x in (182,418):
 for t in (35,191):roofbox('SOLAR Prichytka ramu',x,t,19,7,10,2,silver,2)
# Panel lead is attached to the roof. Fixed socket remains on the rear wall.
tube('SOLAR Kabel k rozpojitelnemu konektoru',[(408,221,202),(450,280,202),(490,382,151),(500,408,90),(500,408,38)],black,2,1)
box('Rozpojitelny konektor panela',495,400,27,10,8,12,black)
modules=[('ESP32-S3 N16R8',385,265,64,28,3,blue),('CN3791 6V',460,265,46,24,5,green),('LiPo 104050 2500mAh',385,305,50,40,4,silver),('MT3608',445,305,38,20,6,blue),('INA219 panel 0x40',491,303,32,25,7,blue),('INA219 bateria 0x41',491,335,32,25,8,blue),('Rele REL300',437,349,52,27,9,blue),('LED a meraci delic',385,351,50,30,16,green)]
with (OUT/'rozmiestnenie-komponentov.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['skupina','nazov','X_mm','Y_mm','Z_mm','sirka_X_mm','hlbka_Y_mm','vyska_Z_mm','presnost'])
 for name,x,y,w,d,g,mat in modules:writer.writerow([g,name,x,y,18,w,d,10 if g==4 else 16 if g==9 else 8,'menovitý rozmer výrobku' if g in (3,4) else 'návrhová rezerva; fyzicky overiť'])
for name,x,y,w,d,g,mat in modules:
 box(name,x,y,18,w,d,10 if g==4 else 1.6,mat,g)
 if g==4:
  box('LiPo ochranny kapton',385,341,18,50,4,10,gold,4)
  tube('LiPo cerveny vodic',[(433,342,24),(438,343,24),(440,334,24)],light,4,.6)
 elif g==3:
  box('ESP32 kovovy RF kryt',x+24,y+4,20,25,20,3,silver,g)
  box('ESP32 USB C',x,y+9,20,8,10,3,silver,g)
  for dx in range(5,61,3):
   for dy in (1,25):box('ESP32 dutinkova lista',x+dx,y+dy,20,1.8,1.8,4,black,g)
 elif g==9:box('Rele modry blok',x+13,y+5,20,21,16,14,blue,g)
 else:
  box(name+' hlavny obvod',x+8,y+5,20,max(8,w/3),8,3,black,g)
  for dx in (2,w-6):box(name+' svorky',x+dx,y+2,20,4,7,5,green,g)
  box(name+' trimr alebo bocnik',x+w-12,y+d-8,20,7,5,3,silver,g)
for x in (130,235,330):
 for y,g in ((77,12),(390,13)):
  box('LED nastenne svietidlo',x-6,y,106,12,3,8,dark,g)
  box('LED difuzor',x-4,y-.3,108,8,3.6,3,light,g)
for y in (78,389):tube('Vedenie LED po stene',[(80,y,110),(360,y,110),(360,365,16)],black,15,.6)
control=box('C01 Ovladaci panel 100x40x4',30,18,23,100,40,4,dark,14)
for x in (56,96):hole(control,x,36,25,3,10)
hole(control,119,36,25,1.5,10)
for x,y in ((35,23),(125,23),(35,53),(125,53)):
 hole(control,x,y,25,1.6,10)
 box('C01 Distancny stlpik 15mm',x-2,y-2,8,4,4,15,silver,14)
# Shaft passes through the base; its two switch bodies stay outside the entrance path.
for x in (50,90):
 box('Prepinac svetiel kryt',x,31,14,12,10,8,dark,14)
 box('Prepinac montazny krk',x+3,33,22,6,6,7,silver,14)
 box('Prepinac matica',x+2,32,27,8,8,2,silver,14)
 box('Prepinac svetiel packa',x+4,34,29,4,3,6,silver,14)
box('LED hlavneho zdroja',117.5,34.5,27,3,3,2,blue,17)
def label(text,x,y,size):
 bpy.ops.object.text_add(location=(x/1000,y/1000,.0273));o=bpy.context.object;o.data.body=text;o.data.size=size/1000;o.data.extrude=.00005
 bpy.ops.object.convert(target='MESH');finish(bpy.context.object,'C01 Popis '+text,ivory,14)
label('SVETLA',36,49,5)
label('A',54,22,5);label('B',94,22,5);label('5V',115,25,3.5)
GROUPS={0:'Dom, fasada a priecky',1:'Cela odnimatelna strecha',2:'Panel na streche a jeho uchytenie',3:'ESP32-S3',4:'Chranena LiPo 2500mAh',5:'CN3791',6:'MT3608',7:'INA219 panel',8:'INA219 bateria',9:'Prepinacie rele LED',12:'Svetelny okruh A',13:'Svetelny okruh B',14:'Ovladaci panel svetiel A/B',15:'Vedenie LED',16:'LED a meraci delic',17:'Indikator hlavneho zdroja'}
bpy.context.view_layer.update();meshes=[]
for o in objects:
 o.data.calc_loop_triangles();p=[];n=[]
 for tri in o.data.loop_triangles:
  normal=o.matrix_world.to_3x3()@tri.normal
  for idx in tri.vertices:
   p.extend(round(v*1000,3) for v in o.matrix_world@o.data.vertices[idx].co);n.extend(round(v,4) for v in normal)
 meshes.append(dict(name=o.name,p=p,n=n,c=list(o.data.materials[0].diffuse_color[:3]),g=int(o['group'])))
asset=dict(units='mm',base=[600,450,8],house=[480,330,120],roof_angle_deg=35,roof_groups=[1,2],panel_size_mm=[230,195,17],groups=GROUPS,meshes=meshes,module_envelopes_only=True)
for dest in (ROOT/'frontend/house/model.json',OUT/'3d/model.json'):dest.write_text(json.dumps(asset,separators=(',',':')))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'3d/dom.glb'),export_format='GLB',use_selection=True)
bpy.ops.wm.stl_export(filepath=str(OUT/'3d/dom-mm.stl'),export_selected_objects=True,global_scale=1000)
# Studio objects only in the editable Blender scene, excluded from manufacturing exports.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.011));stage=bpy.context.object;stage.name='STUDIO';stage.data.materials.append(material('Studio',(.82,.83,.81)))
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.84,.9,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
for loc,power,size in (((.15,-.5,1.2),60,1.1),((1,.7,.9),45,.9),((-.5,.6,.7),25,.8)):
 bpy.ops.object.light_add(type='AREA',location=loc);bpy.context.object.data.energy=power;bpy.context.object.data.size=size
bpy.ops.object.camera_add(location=(.98,-.85,.79));cam=bpy.context.object;scene.camera=cam

def camera(loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
camera((.98,-.85,.79),(.30,.225,.11),.84)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=92
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'3d/dom.blend'),compress=True)
def render(name):scene.render.filepath=str(OUT/'nahlady'/name);bpy.ops.render.render(write_still=True)
render('dom-zatvoreny.jpg')
for o in objects:
 if o['group'] in (1,2):o.location.z+=.18;o.location.y+=.05
camera((1,-1,1.3),(.30,.25,.23),1.05);render('dom-strecha-odlozena.jpg')
for o in objects:
 if o['group'] in (1,2):o.hide_render=True
camera((.30,.225,1.8),(.30,.225,0),.70);render('dom-podorys-3d.jpg')
print('DONE: detailed rooftop solar house; ridge',RIDGE,'mm; meshes',len(meshes))
