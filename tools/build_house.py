"""Run: blender -b --python tools/build_house.py. All manufacturing dimensions are mm."""
import bpy, math, json, csv
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'model-domu'; (OUT/'3d').mkdir(parents=True,exist_ok=True); (OUT/'nahlady').mkdir(exist_ok=True)
FRONT=70; BACK=400; FLOOR=8; WALL=120; THICK=6; ANGLE=math.radians(25); RIDGE=128+165*math.tan(ANGLE)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.length_unit='MILLIMETERS'
materials={}
def material(name,color,metal=0,alpha=1):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,alpha); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*(c**2.2 for c in color),alpha);p.inputs['Roughness'].default_value=.58;p.inputs['Metallic'].default_value=metal;p.inputs['Alpha'].default_value=alpha
 if alpha<1: m.surface_render_method='DITHERED'
 materials[name]=m;return m
wood=material('Svetla preglejka',(0.64,.43,.23));wallmat=material('Steny 6 mm',(.79,.61,.39));roofmat=material('Strecha 4 mm',(.13,.16,.20));blue=material('PCB modra',(.025,.19,.34));green=material('PCB zelena',(.035,.28,.17));silver=material('Chranena LiPo',(.73,.74,.73),.35);black=material('Moduly',(.035,.045,.055));yellow=material('LED a bateria',(.95,.64,.12));water=material('Voda orientacna hladina',(.04,.42,.68),0,.50);glass=material('Plastove nadrze',(.6,.8,.88),0,.20);cablemat=material('Vodice',(.14,.16,.17));solar=material('Solarne clanky',(.025,.07,.18),.2)
objects=[]
def box(name,x,y,z,w,d,h,mat=wood,g=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=((x+w/2)/1000,(y+d/2)/1000,(z+h/2)/1000));o=bpy.context.object;o.name=name;o.dimensions=(w/1000,d/1000,h/1000);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);o['group']=g;objects.append(o);return o

def prism(name,verts,faces,mat,g):
 me=bpy.data.meshes.new(name);me.from_pydata([[a/1000 for a in v] for v in verts],[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat);o['group']=g;objects.append(o);return o

def cut(o,x,y,z,w,d,h):
 c=box('temporary_cut',x,y,z,w,d,h);bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Otvor','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);objects.remove(c);bpy.data.objects.remove(c,do_unlink=True)
def hole(o,x,y,z,r,depth,along_y=False):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r/1000,depth=depth/1000,location=(x/1000,y/1000,z/1000),rotation=(math.pi/2,0,0) if along_y else (0,0,0))
 c=bpy.context.object;bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Priechod kabla','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
base=box('P01 Podstava 600x450x8',0,0,0,600,450,8)
for x,y in [(360,85),(360,385),(285,35),(320,35),(500,370)]:hole(base,x,y,4,3,12)
for x in (15,565):
 for y in (15,415):box('Gumova nozicka 10 mm',x,y,-10,20,20,10,black)

f=box('P02 Predna stena 480x120x6',60,70,8,480,6,120,wallmat)
for x in (100,210,420):cut(f,x,69,43,40,8,35)
# The door is only a drawing/overlay, not an opening that weakens the wall.
box('Dvere iba naznacene',310,69.6,8,25,.3,70,wood)
back=box('P03 Zadna stena 480x120x6',60,394,8,480,6,120,wallmat);hole(back,500,397,33,4,10,True)
l=box('P04 Lava stena 318x120x6',60,76,8,6,318,120,wallmat);cut(l,59,135,43,8,40,35);cut(l,59,300,43,8,40,35)
r=box('P05 Prava stena 318x120x6',534,76,8,6,318,120,wallmat);cut(r,533,140,43,8,40,35)
box('P06 Pozdlzna priecka 318x100x6',370,76,8,6,318,100,wallmat)
box('P07 Priecna priecka lava 304x100x6',66,235,8,304,6,100,wallmat)
box('P08 Priecna priecka prava 158x100x6',376,250,8,158,6,100,wallmat)
box('P09 Vyberatelna doska elektroniky 150x132x4',380,257,10,150,132,4)
# Roof as two full panels, two triangular gables and guide battens: one removable assembly.
for sign in (-1,1):
 y0=235; y1=235+sign*196*math.cos(ANGLE); z1=RIDGE-196*math.cos(ANGLE)*math.tan(ANGLE);normal=(0,sign*math.sin(ANGLE)*4,math.cos(ANGLE)*4)
 v=[(48,y0,RIDGE),(552,y0,RIDGE),(552,y1,z1),(48,y1,z1)];v+= [(x+normal[0],y+normal[1],z+normal[2]) for x,y,z in v]
 prism('ROOF P10 panel 504x196x4 '+str(sign),v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],roofmat,1)
for x in (60,536):
 v=[(x,70,128),(x,400,128),(x,235,RIDGE),(x+4,70,128),(x+4,400,128),(x+4,235,RIDGE)]
 prism('ROOF P11 trojuholnikovy stit',v,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],wallmat,1)
for x in (68,522): box('ROOF L01 priecny nosnik 316x10x10',x,77,118,10,316,10,wood,1)
for x in (69,515):
 for y in (85,350):box('ROOF L02 vodiaci doraz 30x10x6',x,y,122,10,30,6,wood,1)
# Reserved module envelopes. Actual screw holes must be transferred from purchased boards.
modules=[('ESP32-S3 N16R8',385,265,64,28,3,blue),('CN3791 6V',460,265,46,24,5,green),('LiPo 104050 2500mAh',385,305,50,40,4,silver),('MT3608',445,305,38,20,6,blue),('INA219 panel 0x40',491,303,32,25,7,blue),('INA219 bateria 0x41',491,335,32,25,8,blue),('Rele REL300',437,349,52,27,9,blue),('DRV8833',497,367,28,20,10,green),('Univerzalka LED a delic',385,351,50,30,16,green)]
for name,x,y,w,d,g,mat in modules:
 o=box(name,x,y,18,w,d,10 if g==4 else 3,mat,g)
 if g!=4:box(name+' hlavny prvok',x+4,y+4,21,max(8,w/3),max(6,d/2),5,black,g)
 else:box('LiPo izolovana horna cast',385,341,18,50,4,10,yellow,4)
for x in (130,235,330):
 box('LED A na pevnej prednej stene',x,77,112,5,3,3,yellow,12)
 box('LED B na pevnej zadnej stene',x,390,112,5,3,3,yellow,13)
box('Vodice LED A',80,78,110,280,1.5,1.5,cablemat,15);box('Vodice LED B',80,389,110,280,1.5,1.5,cablemat,15)
for x in (280,315):box('Prepinac svetiel SMTS102',x,30,8,12,10,12,silver,14)
# Separate solar stand, dimensioned for the real 230x195 mm panel.
box('P12 Podstava solara 250x150x8',-210,160,0,250,150,8,wood,2)
p=box('Panel 6V5W 230x195x17',-200,180,20,230,195,17,black,2);p.rotation_euler[0]=math.radians(55);p.location=(-.085,.235,.100)
cell=box('Povrch solara',-200,180,20,222,187,1,solar,2);cell.rotation_euler[0]=math.radians(55);cell.location=p.location+Vector((0,-math.sin(math.radians(55))*.009,math.cos(math.radians(55))*.009))
for x in (-175,-15):
 v=[(x,186,8),(x,298,8),(x,298,175),(x,186,15),(x+6,186,8),(x+6,298,8),(x+6,298,175),(x+6,186,15)]
 prism('P14 bocnica stojana solara 112x167x6',v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],wood,2)
# Water module outside house. Reservoir shapes are envelopes, not pressure vessels to print.
box('P13 Podstava vodneho modulu 280x160x8',590,160,0,280,160,8,wood,11)
box('Zachytna vanicka dno',598,166,8,266,148,2,glass,11)
for x in (598,861):box('Zachytna vanicka bocnica',x,166,8,3,148,60,glass,11)
for y in (166,311):box('Zachytna vanicka celo',598,y,8,266,3,60,glass,11)
for x in (608,772):
 box('Nadrz dno 80x80',x,190,10,80,80,2,glass,11)
 for xx in (x,x+78):box('Nadrz stena',xx,190,12,2,80,108,glass,11)
 for yy in (190,268):box('Nadrz stena',x,yy,12,80,2,108,glass,11)
 box('Voda orientacna hladina',x+2,192,12,76,76,42,water,11)
 box('Plavak hladiny schematicky',x+58,242,24,10,10,52,silver,11)
box('Plavak hornej hladiny',782,242,66,10,10,52,silver,11)
box('Plavak vo vanicke',850,284,15,10,10,52,silver,11)
box('Pumpa 5V schematicka',618,202,14,24,24,40,black,11)
box('Filter iba rozmerova rezerva',710,202,12,40,40,100,glass,11)
def tube(name,points):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=.003;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for point,xyz in zip(sp.points,points):point.co=tuple(v/1000 for v in xyz)+(1,)
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(water);o['group']=11;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');objects.append(bpy.context.object)
tube('T01 hadicka pumpa filter',[(635,214,54),(635,214,128),(710,214,128),(730,214,110)])
tube('T02 hadicka filter ciel',[(730,230,110),(730,230,135),(812,230,135),(812,230,125)])
# Render and export consistent model meshes.
# Leave 10 mm between the three removable bases; none may overlap the house.
for o in objects:
 if int(o.get('group',0))==2:o.location.x-=.050
 if int(o.get('group',0))==11:o.location.x+=.020
GROUPS={0:'Dom a priecky',1:'Cela odnimatelna strecha',2:'Solar na samostatnom stojane',3:'ESP32-S3',4:'Chranena LiPo 2500mAh',5:'CN3791 solarna nabijacka',6:'MT3608 zaloznych 5V',7:'INA219 panel',8:'INA219 bateria',9:'Rele pre svetla',10:'DRV8833 cerpadlo',11:'Voda mimo domu',12:'Svetelny okruh A',13:'Svetelny okruh B',14:'Dva prepinace svetiel',15:'Vodice LED',16:'Univerzalka LED a delic'}
bpy.context.view_layer.update()
meshdata=[]
for o in objects:
 o.data.calc_loop_triangles();positions=[];normals=[]
 for tri in o.data.loop_triangles:
  for idx in tri.vertices:
   v=o.matrix_world@o.data.vertices[idx].co;positions.extend(round(c*1000,3) for c in v);n=o.matrix_world.to_3x3()@tri.normal;normals.extend(round(c,4) for c in n)
 meshdata.append({'name':o.name,'p':positions,'n':normals,'c':list(o.data.materials[0].diffuse_color[:3]),'g':int(o['group'])})
asset={'units':'mm','base':[600,450,8],'house':[480,330,120],'roof_angle_deg':25,'groups':GROUPS,'meshes':meshdata,'module_envelopes_only':True}
(ROOT/'frontend'/'house').mkdir(exist_ok=True);(ROOT/'frontend'/'house'/'model.json').write_text(json.dumps(asset,separators=(',',':')))
(OUT/'3d'/'model.json').write_text(json.dumps(asset,separators=(',',':')))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'3d'/'dom.glb'),export_format='GLB',use_selection=True)
bpy.ops.wm.stl_export(filepath=str(OUT/'3d'/'dom-mm.stl'),export_selected_objects=True,global_scale=1000)
# Neutral studio stage, excluded from exported asset above.
material('Pozadie',(.83,.86,.9));box('Render studio iba podklad',-4000,-4000,-18,8000,8000,8,materials['Pozadie'])
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.94,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3
for loc,energy,size in [((.1,-.5,1.8),18,1.6),((1.1,.7,1.2),12,1.2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);li=bpy.context.object;li.data.energy=energy;li.data.shape='DISK';li.data.size=size
bpy.ops.object.camera_add(location=(1.00,-.90,2.40));cam=bpy.context.object;direction=Vector((.30,.23,.10))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.38;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='JPEG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.quality=88;scene.render.filepath=str(OUT/'nahlady'/'dom-zatvoreny.jpg');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'3d'/'dom.blend'),compress=True);bpy.ops.render.render(write_still=True)
for o in objects:
 if o.get('group')==1:o.location.z+=.200;o.location.y+=.200
scene.render.filepath=str(OUT/'nahlady'/'dom-strecha-odlozena.jpg');bpy.ops.render.render(write_still=True)
for o in objects:
 if o.get('group')==1:o.hide_render=True
cam.location=(.30,.23,1.8);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=1.2
scene.render.filepath=str(OUT/'nahlady'/'dom-podorys-3d.jpg');bpy.ops.render.render(write_still=True)
print('DONE house: GLB, BLEND, JSON, two renders. Ridge height mm:',RIDGE)
