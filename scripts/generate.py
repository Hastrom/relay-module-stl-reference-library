#!/usr/bin/env python3
"""AI-generated code (ChatGPT by OpenAI), relay enclosure-fit STL reference library v0.2.
Reconstructed approximate geometry, NOT manufacturer PCB/CAD data.
No vendor mesh/3D assets are downloaded or embedded.
"""
from __future__ import annotations
import math, os, csv, json, zipfile
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import Polygon,Point
import trimesh
from trimesh import transformations
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
os.makedirs(ROOT,exist_ok=True)
PCBH=1.6
# dimensions and mounting hole centers (origin lower left, X main length, Y width)
SPECS=[
 dict(id='01CH_Blue_50x26_4hole',ch=1,w=50.0,h=26.0,holes=[(2.75,2.75),(47.25,2.75),(2.75,23.25),(47.25,23.25)],dia=3.1, hole_status='documented 44.5 x 20.5 pitch', src='https://manuals.plus/asin/B079FJSYGY',variant='opto_ch01',pcb_conf='listed 50 x 26'),
 dict(id='01CH_Blue_50x26_2hole',ch=1,w=50,h=26,holes=[(2.75,2.75),(47.25,23.25)],dia=3.1, hole_status='hole locations reconstructed; only TWO holes documented',src='https://shillehtek.com/blogs/shillehtek-product-manuals/1-channel-5v-relay-module-manual',variant='opto_ch01',pcb_conf='approx. 50 x 26'),
 dict(id='01CH_Red_HL_50p8x25p6',ch=1,w=50.8,h=25.6,holes=[(3.2,3.1),(47.6,3.1),(3.2,22.5),(47.6,22.5)],dia=3.0,hole_status='hole centers estimated from dimensioned marketplace illustration; NOT manufacturer drill data',src='https://www.techmaze.ae/shop/99190408-relay-1-channel-module-board-5v-with-optocoupler-red-highlow-26104',variant='red_dual_terminal',pcb_conf='50.8 x 25.6 from dimensioned module drawing/photo'),
 dict(id='01CH_KY019_HW482_34x27',ch=1,w=34,h=27,holes=[(3.2,3.2),(30.8,23.8)],dia=3.0,hole_status='estimated positions, nominal diameter',src='https://community.element14.com/technologies/embedded/w/documents/4460/ky-019-relay-board-documentation',variant='compact_ky019',pcb_conf='documented 34 x 27'),
 dict(id='01CH_Slim_40x18',ch=1,w=40,h=18,holes=[],dia=3.0,hole_status='mounting holes deliberately omitted; product spec does not establish drilling coordinates',src='https://docs.sunfounder.com/projects/vincent-kit/en/latest/components/component_relay_module.html',variant='slim_no_opto',pcb_conf='documented 40 x 18'),
 dict(id='01CH_Grove_Relay_42x24',ch=1,w=42,h=24,holes=[(1.7,12.0),(35.8,3.1),(35.8,20.9)],dia=2.8,hole_status='reconstructed from photos; NOT confirmed drill data',src='https://wiki.seeedstudio.com/Grove-Relay/',variant='grove',pcb_conf='documented bounding box 42 x 24'),
 dict(id='02CH_Opto_50x41',ch=2,w=50,h=41,holes=[(2.75,2.75),(47.25,2.75),(2.75,38.25),(47.25,38.25)],dia=3.1,hole_status='documented 44.5 x 35.5 pitch',src='https://manuals.plus/asin/B079FGPC9Y',variant='multiple',pcb_conf='documented 50 x 41'),
 dict(id='04CH_Opto_75x55',ch=4,w=75,h=55,holes=[(3.5,3.5),(71.5,3.5),(3.5,51.5),(71.5,51.5)],dia=3.0,hole_status='documented 68 x 48 pitch',src='https://kamami.pl/en/modules-with-power-outputs/1202350-4-channel-relay-module-with-optical-5902186334021.html',variant='multiple',pcb_conf='documented 75 x 55'),
 dict(id='06CH_Opto_103x53',ch=6,w=103,h=53,holes=[(3,3),(100,3),(3,50),(100,50)],dia=3.0,hole_status='estimated 4 corners; verify physical board',src='https://deluxcnc.eu/en/relay/249-6-channel-relay-board-module-5v.html',variant='multiple',pcb_conf='listed 103 x 53 but clone variability'),
 dict(id='08CH_Opto_138x56',ch=8,w=138,h=56,holes=[(3,3),(135,3),(3,53),(135,53)],dia=3.0,hole_status='documented 132 x 50 pitch',src='https://distancionka.com/ua/catalog/radiokomponenty/rele/modul-rele-8-mi-kanalnyy-5v/',variant='multiple',pcb_conf='documented 138 x 56'),
 dict(id='16CH_Opto_180x90',ch=16,w=180,h=90,holes=[(4,4),(176,4),(4,86),(176,86)],dia=3.0,hole_status='hole diameter listed ~3; XY positions estimated',src='https://www.berry-base.pro/en/5v-16-channel-relay-module',variant='multiple',pcb_conf='documented 180 x 90')
]

def circ(x,y,r,n=64):return [(x+r*math.cos(2*math.pi*k/n),y+r*math.sin(2*math.pi*k/n)) for k in range(n)]

def pcb_polygon(s):
 # only an envelope rectangle for Grove; exact notched outline is not known
 return [(0,0),(s['w'],0),(s['w'],s['h']),(0,s['h'])]

def pcb_mesh(s):
 boundary=pcb_polygon(s); rings=[circ(x,y,s['dia']/2) for x,y in s['holes']]
 poly=Polygon(boundary,holes=rings)
 if not poly.is_valid:raise ValueError((s['id'],'invalid board polygon'))
 pts=list(boundary)+sum(rings,[])
 for x in np.arange(1.25,s['w']-0.01,3.5):
  for y in np.arange(1.25,s['h']-0.01,3.5):
   if poly.contains(Point(x,y)):pts.append((float(x),float(y)))
 pts=np.array(pts,float); faces=[]
 for a,b,c in Delaunay(pts).simplices:
  if poly.covers(Polygon(pts[[a,b,c]])) and abs(np.cross(pts[b]-pts[a],pts[c]-pts[a]))>1e-8:faces.append((a,b,c))
 nv=len(pts);verts=np.r_[np.c_[pts,np.zeros(nv)],np.c_[pts,np.full(nv,PCBH)]]
 f=[]
 for a,b,c in faces:f.extend([[a,c,b],[a+nv,b+nv,c+nv]])
 # both exterior and holes drawn same face winding procedure as existing library
 # mesh export accepted by CAD as triangle soup; top/bottom and sides maintain correct edges.
 for ii,ring in enumerate([boundary]+rings):
  for k,a in enumerate(ring):
   b=ring[(k+1)%len(ring)];ia=np.where(np.all(np.isclose(pts,a,atol=1e-8),axis=1))[0][0];ib=np.where(np.all(np.isclose(pts,b,atol=1e-8),axis=1))[0][0]
   if ii==0:f.extend([[ia,ib,ib+nv],[ia,ib+nv,ia+nv]])
   else:f.extend([[ib,ia,ia+nv],[ib,ia+nv,ib+nv]])
 m=trimesh.Trimesh(vertices=verts,faces=f,process=True)
 return m

def mkbox(x,y,z,l,w,h):
 m=trimesh.creation.box(extents=(l,w,h));m.apply_translation((x,y,z+h/2));return m

def cyl(x,y,z,r,h,sections=24):
 m=trimesh.creation.cylinder(radius=r,height=h,sections=sections);m.apply_translation((x,y,z+h/2));return m

rows=[]; summary=[]
for s in SPECS:
 id=s['id']; folder=os.path.join(ROOT,id);os.makedirs(folder,exist_ok=True)
 p=pcb_mesh(s); p.export(os.path.join(folder,id+'_PCB_MOUNTING.stl'))
 meshes=[p]; records=[]; ch=s['ch']
 def component(name,center,size,kind='box',confidence='reconstructed',**kwargs):
  x,y,z=center; sx,sy,sz=size
  if kind=='cyl':m=cyl(x,y,z,sx/2,sz)
  else:m=mkbox(x,y,z,sx,sy,sz)
  meshes.append(m)
  records.append(dict(id=id,feature=name,x_mm=round(x,3),y_mm=round(y,3),z_from_pcb_bottom_mm=round(z,3),length_mm=sx,width_mm=sy,height_mm=sz,evidence=confidence))
  return m
 def header(name,x,y,count,axis='y',pinheight=7.8):
  pitch=2.54
  sl,sw=(count*pitch,2.54) if axis=='x' else (2.54,count*pitch)
  component(name+'_insulator',(x,y,PCBH),(sl,sw,2.5),confidence='reconstructed connector placement; 2.54 pitch is standard')
  for j in range(count):
   px=x+(j-(count-1)/2)*pitch if axis=='x' else x
   py=y+(j-(count-1)/2)*pitch if axis=='y' else y
   component(name+'_pin'+str(j+1),(px,py,PCBH+2.5),(0.64,0.64,pinheight-2.5),confidence='2.54 mm pin pitch, header placement approximate')
 def terminal(name,x,y,pins=3,axis='y'):
  length=pins*5.08
  sx,sy=(length,9.5) if axis=='x' else (9.5,length)
  component(name,(x,y,PCBH),(sx,sy,10.8),confidence='footprint centers reconstructed; pitch nominal 5.08 mm')
  # well-defined screw-head envelope (screw cap raised by 0.3mm)
  for j in range(pins):
   px=x+(j-(pins-1)/2)*5.08 if axis=='x' else x
   py=y+(j-(pins-1)/2)*5.08 if axis=='y' else y
   component(name+'_screw'+str(j+1),(px,py,PCBH+10.8),(3.4,3.4,.35),kind='cyl',confidence='approx screw-head envelope')
 def relay(name,x,y,orient='y',rkind='songle'):
  if rkind=='omron':dims=(19.8,15.8,15.8)
  elif rkind=='grove':dims=(19.5,15.2,15.5) # not guaranteed HLS8-T73 dims
  else:dims=(19.1,15.5,15.3) # Songle SRD datasheet body MAX-ish
  if orient=='y':dims=(dims[1],dims[0],dims[2])
  component(name,(x,y,PCBH),dims,confidence=('datasheet relay body dimensions; module placement reconstructed'))
 def opto(name,x,y):component(name,(x,y,PCBH),(4.6,6.5,3.6),confidence='PC817 type package dimensions approximate; placement reconstructed')
 def resistor(name,x,y):component(name,(x,y,PCBH),(2.0,1.15,.65),confidence='representative SMD envelope; placement reconstructed')
 def led(name,x,y):component(name,(x,y,PCBH),(2.0,2.0,1.5),confidence='representative LED envelope; placement reconstructed')
 def transistor(name,x,y):component(name,(x,y,PCBH),(3.0,3.0,4.5),kind='cyl',confidence='representative TO92 envelope; placement reconstructed')
 if s['variant'] in ('opto_ch01','red_dual_terminal'):
  # top view: low voltage left, switching output right
  relay('K1_SRD',25.0,13.0,'y')
  terminal('J_OUT',43.1,13.0,3,'y')
  
  if s['variant']=='red_dual_terminal':
   component('U1_SMD_opto',(12.9,20.8,PCBH),(3.6,4.0,2.0),confidence='SMD optocoupler approximate package; reconstructed')
   led('LED1',7.8,24.0)
  else:
   opto('U1',10.8,17.6);led('LED1',10.2,24.0)
  resistor('R1',13.0,7.0)
  if s['variant']=='red_dual_terminal':
   terminal('J_IN',6.2,13.0,3,'y')
   # jumper on red board close to input, simplified vertical headers
   header('JP_HL',13.0,3.0,2,'y',6.3)
  else:
   header('J_IN',7.0,7.0,3,'y');transistor('Q1',12.0,11.0)
 elif s['variant']=='compact_ky019':
  relay('K1_JQC',20.0,13.7,'x') # 19.1 x 15.5 on 34x27 footprint
  terminal('J_OUT',5.6,13.5,3,'y')
  # right side header perpendicular to x direction as in board photo; 3 open pins
  header('J_IN',31.9,13.0,3,'y',7.6)
  led('LED1',25.6,23.9);transistor('Q1',14.5,23.7)
 elif s['variant']=='slim_no_opto':
  relay('K1_SRD',20.5,9,'x')
  terminal('J_OUT',35.0,9,3,'y')
  header('J_IN',4.5,8.9,3,'y')
  led('LED1',9.1,16.0);resistor('R1',9.1,2.0)
 elif s['variant']=='grove':
  relay('K1_relay',23.8,12,'x','grove')
  terminal('J_OUT',9.0,12,2,'y')
  component('GROVE_4PIN_SOCKET',(38,12,PCBH),(7.0,9.0,6.0),confidence='connector mechanical envelope approximate')
  led('LED1',13.0,22.0)
 elif ch==2:
  for j,y in enumerate([11.0,30.0],1):
   relay('K'+str(j),26.0,y,'x');terminal('J_OUT'+str(j),40.5,y,3,'y');opto('U'+str(j),11.0,y);led('LED'+str(j),11.0,y-6)
  header('J_IN',6.3,20.5,4,'y')
 else:
  if ch==16:
   xs=np.linspace(14,166,8)
   for j,(x,y,ty) in enumerate([(x,26.5,6.1) for x in xs]+[(x,64,83.9) for x in xs],1):
    relay('K'+str(j),float(x),y,'y')
    terminal('J_OUT'+str(j),float(x),ty,3,'x')
    opto('U'+str(j),float(x),40.3 if j<=8 else 50.7);led('LED'+str(j),float(x),14.0 if j<=8 else 76.5)
   header('J_IN',90,45,18,'x') # pin row may overlap optos near x=90 but separate in 3D, flagged
   terminal('J_POWER',174.7,45,2,'y')
  else:
   n=ch; edge_margin=12.7 if ch==4 else 12.3;xs=np.linspace(edge_margin,s['w']-edge_margin,n)
   # use songle enclosure aligned across x short dimension 15.5, terminals on upper margin
   ry=s['h']*.57;ty=s['h']-6.0;oy=s['h']*.22
   for j,x in enumerate(xs,1):
    relay('K'+str(j),float(x),ry,'y');terminal('J_OUT'+str(j),float(x),ty,3,'x');opto('U'+str(j),float(x),oy);led('LED'+str(j),float(x),oy+6.5)
   # input header placed low side as an across-x row
   header('J_IN',s['w']/2,3.5,n+2,'x')
  
 full=trimesh.util.concatenate(meshes)
 full.export(os.path.join(folder,id+'_ASSEMBLY.stl'))
 for j,(x,y) in enumerate(s['holes'],1):
  rows.append(dict(id=id,feature=f'HOLE_{j}',x_mm=round(x,3),y_mm=round(y,3),z_from_pcb_bottom_mm=0,length_mm=s['dia'],width_mm=s['dia'],height_mm=PCBH,evidence=s['hole_status']))
 rows+=records
 ext=np.round(full.extents,4).tolist()
 entry=dict(id=id,channels=ch,board_mm=[s['w'],s['h'],PCBH],hole_centers_mm=s['holes'],hole_diameter_mm=s['dia'],mounting_claim=s['hole_status'],pcb_claim=s['pcb_conf'],component_position_claim='RECONSTRUCTED, NOT PCB CAD VERIFIED',component_height_claim='relay datasheet body envelope, other parts representative',source=s['src'],module_style=s['variant'],assembly_extents_xyz_mm=ext,pcb_watertight=bool(p.is_watertight),assembly_watertight=bool(full.is_watertight),triangle_count_assembly=len(full.faces),overhang_notes='Terminals/components may overhang PCB; envelope independent of wiring clearance')
 summary.append(entry)
 # include coordinate CSV per board
 with open(os.path.join(folder,id+'_COORDINATES.csv'),'w',newline='',encoding='utf-8') as f:
  W=csv.DictWriter(f,fieldnames=list(rows[-len(records):][0].keys()) if records else list(rows[-1].keys()))
  W.writeheader()
  for r in rows[-len(records):]:W.writerow(r)
 print(id, 'ch',ch,'board',s['w'],s['h'],'holes',len(s['holes']),'components',len(records),'extent',ext,'watertight',p.is_watertight)

with open(os.path.join(ROOT,'ALL_FEATURE_COORDINATES.csv'),'w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
with open(os.path.join(ROOT,'accuracy_sources.json'),'w',encoding='utf-8') as f:json.dump(summary,f,indent=2,ensure_ascii=False)
with open(os.path.join(ROOT,'README_RU.txt'),'w',encoding='utf-8') as f:
 f.write('БЕСПЛАТНАЯ STL-БИБЛИОТЕКА РЕЛЕЙНЫХ МОДУЛЕЙ ДЛЯ ARDUINO — ВЕРСИЯ 0.2\n')
 f.write('11 различных механических исполнений: шесть 1-канальных + 2,4,6,8,16 каналов. Каждый каталог: STL печатной платы с отверстиями, STL сборки, таблица 3D-координат компонентов.\n\n')
 f.write('СИСТЕМА КООРДИНАТ: мм. X — длина платы, Y — ширина. (0,0,0) — нижний левый угол нижней поверхности PCB. Толщина PCB условно 1.6 мм. Верх платы Z=1.6 мм.\n')
 f.write('ВАЖНО: Это модели для ПРЕДВАРИТЕЛЬНОГО проектирования КОРПУСОВ, не сканированные и не восстановленные из исходных CAD данных производителя конкретной платы.\n')
 f.write('Габариты плат и указанные межосевые расстояния крепления взяты из спецификаций по ссылкам; все неподтвержденные центры отверстий, размещение реле, клемм, разъемов и мелких деталей отмечены как reconstructed или estimated.\n')
 f.write('Общий габарит типа KY019 и Grove подтвержден, но форма контура Grove заменена габаритным прямоугольником, крепежные отверстия у него реконструированы.\n')
 f.write('Размер пластикового корпуса реле Songle: 19.1 x 15.5 x 15.3 мм по datasheet. Размеры и высоты остальных корпусов типовые, не измерены на каждой плате.\n')
 f.write('Не используйте как рабочие чертежи для ЧПУ и не сверлите без проверки зазоров и сопоставления с реальным экземпляром.\n')
 f.write('STL не содержит данных о электрической изоляции; при сетевом напряжении оставляйте необходимые расстояния и защиту по нормам.\n\n')
 f.write('Происхождение: самостоятельное процедурное построение; чужих 3D-моделей в архиве нет. Созданный код и модели без ограничений на использование (CC0); ссылки на источники фактов/размеров в accuracy_sources.json.\n')
 f.write('Размеры реле (datasheet): https://naylampmechatronics.com/img/cms/000263/SRD-05VDC-SL-C-Datasheet.pdf\n')
 f.write('Публичной публикации в чужом или пользовательском репозитории НЕ производилось.\n')
 f.write('Проверять при реальном проектировании: отверстия, USB (если есть), клеммы с учетом вводимых проводов, ширины каналов изоляции, выступающие снизу контакты.\n')
with open(os.path.join(ROOT,'LICENSE_CC0.txt'),'w',encoding='utf-8') as f:f.write('Self-authored procedural STL meshes and generator script: dedicated to the public domain under CC0 1.0. No endorsement by hardware vendors. https://creativecommons.org/publicdomain/zero/1.0/\n')
zip_file=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rebuild_output_v02.zip'))
with zipfile.ZipFile(zip_file,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
 for dirpath,_,files in os.walk(ROOT):
  for name in sorted(files):
   full=os.path.join(dirpath,name);z.write(full,arcname=os.path.relpath(full,ROOT))
print('ZIP',zip_file,os.path.getsize(zip_file),'filecount',len(z.namelist()) if False else 'done')
