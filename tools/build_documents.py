"""Generate manufacturing CSV, full-size SVG templates, floor plan and A3 PDF."""
from pathlib import Path
import csv,math,json,html,os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'model-domu';V=OUT/'vykresy';V.mkdir(exist_ok=True)
parts=[
('P01','Podstava domu',1,600,450,8,'preglejka','4 nožičky 10 mm; otvory káblov podľa pôdorysu'),
('P02','Predná stena',1,480,120,6,'preglejka','3 okná 40x35; dvere iba naznačiť'),
('P03','Zadná stena',1,480,120,6,'preglejka','káblový otvor Ø8 pri technickej miestnosti'),
('P04','Ľavá stena',1,318,120,6,'preglejka','2 okná 40x35'),
('P05','Pravá stena',1,318,120,6,'preglejka','1 okno 40x35'),
('P06','Pozdĺžna priečka',1,318,100,6,'preglejka','výška 100; horných 20 mm necháva prístup'),
('P07','Ľavá priečna priečka',1,304,100,6,'preglejka','kolmo medzi ľavú stenu a P06'),
('P08','Pravá priečna priečka',1,158,100,6,'preglejka','oddeľuje technickú miestnosť'),
('P09','Vyberateľná doska elektroniky',1,150,132,4,'preglejka','dosky uchytiť na dištančné stĺpiky'),
('P10','Rovina strechy',2,504,196,4,'preglejka','sklon 25°; spoj prekryť páskou 20 mm'),
('P11','Štít strechy',2,330,77,4,'preglejka','trojuholník, vrchol uprostred 165 mm'),
('P12','Podstava solára',1,250,150,8,'preglejka','samostatná odnímateľná časť'),
('P13','Podstava vody',1,280,160,8,'preglejka','vanička a nádržky sú kúpené nádoby'),
('P14','Bočnica solárneho stojana',2,112,167,6,'preglejka','tvar podľa SVG, predná výška 7 mm, zadná 167 mm'),
('L01','Nosník strechy',2,316,10,10,'lišta','spája štíty a tvorí jeden kus strechy'),
('L02','Vodiaci doraz strechy',4,30,10,6,'lišta','len dorazy, vôľa aspoň 0,5–1 mm'),
]
with (OUT/'rezaci-plan.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['ID','diel','kusy','dlzka_mm','sirka_mm','hrubka_mm','material','poznamka']);w.writerows(parts)
# SVGs have physical mm dimensions: print/export at 100%, never fit to page.
windows={'P02':[(40,35,40,35),(150,35,40,35),(360,35,40,35)],'P04':[(59,35,40,35),(224,35,40,35)],'P05':[(64,35,40,35)]}
for id,name,count,w,h,t,mat,note in parts:
 if id.startswith('L'):continue
 shape=f'<rect x="0" y="0" width="{w}" height="{h}"/>'
 if id=='P11':shape='<polygon points="0,77 330,77 165,0"/>'
 if id=='P14':shape='<polygon points="0,167 112,167 112,0 0,160"/>'
 holes=''.join(f'<rect x="{x}" y="{h-y-hh}" width="{ww}" height="{hh}"/>' for x,y,ww,hh in windows.get(id,[]))
 if id=='P03':holes+='<circle cx="440" cy="95" r="4"/>'
 if id=='P01':
  for x,y in [(360,85),(360,385),(285,35),(320,35),(500,370)]:holes+=f'<circle cx="{x}" cy="{h-y}" r="3"/>'
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"><title>{id} {html.escape(name)} – 1:1 mm</title><g fill="none" stroke="black" stroke-width="0.15">{shape}{holes}</g><text x="10" y="15" font-size="5" font-family="sans-serif">{id} · {w} x {h} x {t} mm · {count} ks · 1:1</text><path d="M10 {h-8} h100" stroke="blue" stroke-width="0.3"/><text x="10" y="{h-10}" font-size="4">Kontrolná mierka 100 mm</text></svg>'''
 (V/f'{id}-1ku1.svg').write_text(svg)
wire=[('W01','LAB +5 V → hlavný rozvod',1,600,'0,5 mm²','červený'),('W02','LAB GND → spoločná zem',1,600,'0,5 mm²','čierny'),('W03','Batéria → INA219 0x41',2,150,'0,25–0,5 mm²','PH2.0 adaptér, polaritu zmerať'),('W04','INA219 → batériový uzol',1,120,'0,25–0,5 mm²','červený'),('W05','CN3791 BAT → batériový uzol',2,150,'0,25–0,5 mm²','pár + / GND'),('W06','Batériový uzol → MT3608 cez servisnú prepojku',2,150,'0,25–0,5 mm²','odpoj na úplné prednabitie'),('W07','MT3608 5 V → relé NC',1,150,'0,25–0,5 mm²','červený'),('W08','Hlavný +5 V → relé NO a VCC',2,150,'0,25–0,5 mm²','červený'),('W09','Relé COM → LED vetva A',2,750,'0,14–0,25 mm²','napájanie a spínaný návrat'),('W10','Relé COM → LED vetva B',2,500,'0,14–0,25 mm²','napájanie a spínaný návrat'),('W11','Rozvod 3 LED A na stene',2,300,'0,14 mm²','každá LED vlastný 330 Ω'),('W12','Rozvod 3 LED B na stene',2,300,'0,14 mm²','každá LED vlastný 330 Ω'),('W13','Prepínač A → GPIO5/GND',2,600,'0,14 mm²','signálový pár'),('W14','Prepínač B → GPIO6/GND',2,600,'0,14 mm²','signálový pár'),('W15','MT3608 → ESP napájací USB-C kábel',1,200,'hotový kábel','iba overených 5 V'),('W16','I²C ESP → INA219 0x40',4,180,'0,14 mm²','3V3 GND SDA SCL'),('W17','I²C INA219 0x40 → 0x41',4,100,'0,14 mm²','3V3 GND SDA SCL'),('W18','Panel → INA219 panel',2,600,'0,25–0,5 mm²','vrátane pôvodného kábla panela'),('W19','Panelový INA219 → CN3791 IN',2,150,'0,25–0,5 mm²','vstup nikdy na BAT'),('W20','DRV8833 → pumpa',2,450,'0,25–0,5 mm²','motorový pár, viesť mimo I²C'),('W21','Hlavný zdroj → DRV8833',2,200,'0,25–0,5 mm²','+5 V / GND'),('W22','Predĺženie štyroch plavákov',8,300,'0,14–0,25 mm²','nadstavuje existujúce káble snímačov'),('W23','GPIO12 → DRV8833 AIN1',1,180,'0,14 mm²','AIN2 na GND'),('W24','GPIO4 delič a tranzistory LED',8,150,'0,14 mm²','miestne prepojky')]
with (OUT/'dlzky-vodicov.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['ID','spoj','pocet_vodicov','dlzka_jedneho_mm','prierez','poznamka']);w.writerows(wire)
with (OUT/'hadicky.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['ID','odkial','kam','dlzka_mm','poznamka']);w.writerows([('T01','pumpa','vstup filtra',220,'rezervu uprav až po osadení nádob'),('T02','výstup filtra','cieľová nádrž',220,'koniec hadičky zaisti nad maximálnou hladinou'),('T03','zvyšok','rezerva',60,'spolu 500 mm zo sady')])
# Floor plan, with every purchased module identified and accessible from above.
labels=[('ESP',385,265,64,28),('CN3791',460,265,46,24),('LiPo',385,305,50,40),('MT3608',445,305,38,20),('INA40',491,303,32,25),('INA41',491,335,32,25),('RELÉ',437,349,52,27),('DRV',497,367,28,20),('LED/ADC',385,351,50,30)]
rects=[(0,0,600,450,'#f8f1e7'),(60,70,480,330,'#e3c69b'),(66,76,468,318,'#fffaf2'),(370,76,6,318,'#b58a55'),(66,235,304,6,'#b58a55'),(376,250,158,6,'#b58a55')]
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="330mm" height="260mm" viewBox="-30 -25 660 520"><title>Pôdorys 1:2, všetky rozmery v mm</title>']
for x,y,w,h,col in rects:svg.append(f'<rect x="{x}" y="{450-y-h}" width="{w}" height="{h}" fill="{col}" stroke="#40352b" stroke-width="1"/>')
for name,x,y,w,h in labels:svg.append(f'<rect x="{x}" y="{450-y-h}" width="{w}" height="{h}" fill="#b3cdd9" stroke="#243647" stroke-width="0.7"/><text x="{x+2}" y="{450-y-h+9}" font-size="7" font-family="sans-serif">{name}</text>')
for x in (130,235,330):
 for y in (77,390):svg.append(f'<circle cx="{x}" cy="{450-y}" r="4" fill="#e7a928"/>')
for x in (280,315):svg.append(f'<circle cx="{x}" cy="420" r="5" fill="#475364"/>')
svg+=['<text x="65" y="12" font-size="11" font-family="sans-serif">ZADNÁ STRANA</text>','<text x="65" y="480" font-size="11" font-family="sans-serif">PREDNÁ STRANA · 600 × 450 mm · súradnice od ľavého predného rohu</text>','<text x="85" y="120" font-size="13" font-family="sans-serif">Svetelný okruh B</text>','<text x="85" y="300" font-size="13" font-family="sans-serif">Svetelný okruh A</text>','<text x="380" y="215" font-size="9" font-family="sans-serif">Voľný priestor, bez nábytku</text>','</svg>']
(V/'podorys.svg').write_text(''.join(svg))
# Vector PDF with embedded Unicode font and manufacturing data, A3 landscape.
font_candidates=[os.environ.get('SOC_PDF_FONT',''),
 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
 str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'arial.ttf'),
 '/System/Library/Fonts/Supplemental/Arial.ttf']
font_path=next((p for p in font_candidates if p and Path(p).is_file()),None)
if font_path is None:raise RuntimeError('Nastav SOC_PDF_FONT na cestu k Unicode TTF fontu, napr. DejaVu Sans.')
pdfmetrics.registerFont(TTFont('DejaVu',font_path))
c=canvas.Canvas(str(OUT/'STAVEBNY-NAVOD.pdf'),pagesize=landscape(A3));c.setTitle('SOČ – stavebný návod dreveného smart domu');c.setAuthor('Projekt SOC');PW,PH=landscape(A3)
def heading(title,sub=''):
 c.setFont('DejaVu',20);c.drawString(18*mm,PH-20*mm,title);c.setFont('DejaVu',10);c.drawString(18*mm,PH-28*mm,sub)
def pageend(n):
 c.setFont('DejaVu',8);c.drawString(18*mm,12*mm,f'SOČ · verzia 2026-11-04 · všetky rozmery v mm · strana {n}');c.showPage()
def line(y,text,size=10):c.setFont('DejaVu',size);c.drawString(18*mm,y*mm,text)
heading('Drevený smart dom – stavebný návod','Celé steny · celá strecha sa zdvihne · bez nábytku · odnímateľné bočné moduly')
for image,x in [('dom-zatvoreny.jpg',16),('dom-strecha-odlozena.jpg',210)]:
 p=OUT/'nahlady'/image
 if p.exists():c.drawImage(str(p),x*mm,95*mm,width=195*mm,height=135*mm,preserveAspectRatio=True,mask='auto')
line(75,'Podstava domu 600 × 450 × 8. Dom 480 × 330. Steny 120 vysoké, hrúbka 6. Priečky vysoké 100.')
line(65,'Strecha: sklon 25°, dve roviny 504 × 196 × 4; štíty a dorazy sú súčasťou jedného odnímateľného kusu.')
line(55,'Solárny stojan 250 × 150. Vodný modul 280 × 160. Celková šírka pri bočnom osadení približne 1 150.')
line(45,'Elektronické dosky, filter a nádržky sú rozmerové rezervy. Montážne otvory prenes zo skutočných dielov.')
line(35,'SVG v priečinku vykresy sú 1:1; tento PDF prehľad nie je šablóna 1:1. Pred rezaním zmeraj hrúbku dosiek.')
pageend(1)
heading('Pôdorys a osadenie','Súradnice X/Y od ľavého predného rohu podstavy. Predná strana má dva prepínače.')
scale=.43;ox=20;oy=45
for x,y,w,h,col in rects:
 c.setFillColor(col);c.rect((ox+x*scale)*mm,(oy+y*scale)*mm,w*scale*mm,h*scale*mm,stroke=1,fill=1)
c.setFillColor('#182530')
for name,x,y,w,h in labels:
 c.setFillColor('#b3cdd9');c.rect((ox+x*scale)*mm,(oy+y*scale)*mm,w*scale*mm,h*scale*mm,stroke=1,fill=1);c.setFillColor('#182530');c.setFont('DejaVu',5);c.drawString((ox+(x+1)*scale)*mm,(oy+(y+5)*scale)*mm,name)
for n,(name,x,y,w,h) in enumerate(labels):
 name=labels[n][0];c.setFont('DejaVu',10);c.drawString(290*mm,(220-n*14)*mm,f'{name}: X={x}, Y={y}; rezerva {w} × {h}')
c.setFont('DejaVu',10)
for k,t in enumerate(['Dom: X60–540, Y70–400.','Pozdĺžna priečka: X370–376.','Ľavá priečka: Y235–241.','Pravá priečka: Y250–256.','Doska elektroniky: X380 Y257.','Pod PCB 4 mm izolačné stĺpiky.']):c.drawString(290*mm,(90-k*10)*mm,t)
pageend(2)
heading('Rezací plán','Čisté rozmery hotových dielov. Pripočítaj šírku rezu píly pri rozložení na materiál, nie k hotovému dielu.')
y=250
for row in [('ID','diel','ks','dĺžka','šírka','hrúbka')]+[r[:6] for r in parts]:
 for x,txt in zip([18,40,210,240,280,320],row):c.setFont('DejaVu',10);c.drawString(x*mm,y*mm,str(txt))
 y-=10
line(60,'P11 je trojuholník: základňa 330, výška 77, vrchol X165. P14 je tvarovaný diel; použi jeho SVG.')
line(50,'Strechu zlep do jedného rámu. Spoj rovín hore prekry páskou/tenkou lištou; pred lepením nasucho odskúšaj.')
line(40,'Odnímateľná doska elektroniky 150 × 132: nelep priamo batériu ani spodné kontakty PCB na drevo.')
pageend(3)
heading('Dĺžky vodičov a hadičiek','Predstrihy s rezervou pre trasu po stenách/pod podstavou. Pri prvej montáži skráť až po overení.')
y=250
for id,name,n,l,gauge,note in wire:
 c.setFont('DejaVu',8);c.drawString(18*mm,y*mm,f'{id}   {name}');c.drawString(290*mm,y*mm,f'{n} × {l} mm · {gauge}');y-=7
line(65,'T01 pumpa → filter 220 mm; T02 filter → cieľová nádrž 220 mm; rezerva 60 mm z 500 mm hadičky.')
line(54,'Hadice a výšku filtra prispôsob skutočnému čerpadlu. Koniec výtoku zaisti nad hladinou, aby nevznikol sifón.')
line(43,'Napájanie a motor neveď cez tenké Dupont kontakty. Tie používaj na signály a krátke I²C prepoje.')
pageend(4)
heading('Zapojenie – rozhodujúce uzly','Úplná pinová tabuľka a poradie montáže sú v docs/ZAPOJENIE.md. Batéria sa nepripája priamo na panel ani LAB.')
rows=[
'Panel → INA219 0x40 → CN3791 IN. CN3791 variant 6 V nabíja jediný chránený 1S článok na 4,2 V.',
'CN3791 BAT+ a MT3608 IN+ tvoria batériový uzol → INA219 0x41 VIN+ → VIN− → plus batérie.',
'INA219 meria čistý prúd celého článku. Všetky odbery/nabíjanie musia byť na strane uzla, nie mimo bočníka.',
'MT3608 nastav na 5,00 V pred pripojením ESP32. Menovitý 2 A údaj nie je zaručený výstup pri 3,7 → 5 V.',
'Relé REL300: NO = hlavné +5 V; NC = MT3608 +5 V; COM = LED napájanie. VCC/JD-VCC = hlavné 5 V.',
'Relé IN je pevne na GND. Zapnutý hlavný zdroj pritiahne NO; po vypnutí kontakt prejde na NC.',
'LED A/B: každá LED cez svoj 330 Ω; kolektory 2N2222, emitory GND; GPIO7/10 cez 1 kΩ na bázy.',
'Každá báza má 10 kΩ na GND. Prepínače svetiel: GPIO5/6 proti GND, druhý kontakt na prepínači voľný.',
'Detekcia hlavného zdroja: LAB +5 V → 22 kΩ → GPIO4 → 10 kΩ → GND. Pri 5 V je ADC asi 1,56 V.',
'I²C: GPIO8 SDA, GPIO9 SCL; oba INA219 napájané 3,3 V. Druhému nastav adresu 0x41.',
'Pumpa: LAB +5 V → DRV8833 VM; GPIO12 → AIN1; AIN2 GND; nSLEEP 3V3; pumpa medzi AOUT1/AOUT2.',
'Plaváky: GPIO13 sourceOK, GPIO14 targetLow, GPIO15 targetFull, GPIO16 dryOK; kontakty proti GND.',
'ESP32 je stále na MT3608. Pri slabom solári môže batéria klesať aj vtedy, keď hlavný zdroj napája LED.',
'CN3791 nemá hotový oddelený LOAD výstup. Na úplné prednabitie odpoj MT3608, svetlá aj ESP od článku.',
'Pri úplnom prednabití odpoj panel, napájaj iba CN3791 zo správne nastaveného LAB; potom obnov solár.',
'Nastavenie prúdu CN3791 over podľa článku. Hodnota 4 A MAX na e-shope nie je povolený prúd tejto batérie.',
]
for i,t in enumerate(rows):line(245-i*11,t,9)
pageend(5)
heading('Montáž a prvé spustenie','Postupuj po častiach; elektroniku najprv odskúšaj mimo dreveného domu.')
steps=[
'1. Vyrež a označ P01–P14, nasucho zostav steny; zmeraj skutočnú hrúbku materiálu a šírku rezu.',
'2. Vyrež okná podľa SVG, obrús hrany. Steny lepia na podstavu; krátke bočné steny sú medzi čelnými.',
'3. Pridaj priečky a vyberateľnú dosku elektroniky; tá zostáva dostupná zhora po zdvihnutí strechy.',
'4. Zostav rám strechy a dve roviny do jedného kusu. Dorazy nechaj s vôľou; nepouži pánty ani káble do strechy.',
'5. LED upevni na pevné steny. Každá má vlastný rezistor; horné káble prichyť, aby ich strecha nezachytila.',
'6. Pod podstavu nalep 10 mm nožičky. Signalizačné a napájacie trasy prichyť na spodnú stranu a označ Wxx.',
'7. Menič otestuj s malou skúšobnou záťažou; nastav a zmeraj 5 V. Over polaritu batérie a adresy INA219.',
'8. Zapoj relé a LED, potom ESP. Vyskúšaj výpadok aj pri odpojenej Wi-Fi; prepnutie nesmie vyžadovať server.',
'9. Vodnú vaničku otestuj samostatne s čistou vodou. Nádržky, snímače a filter upevni proti prevráteniu.',
'10. Otestuj plaváky a DRV8833; až potom povoľ WATER_ENABLED=1 vo firmvéri a vodný okruh v aplikácii.',
'11. Na PC spusti aplikáciu a Ollamu. ESP a PC pripoj do rovnakej Wi-Fi/LAN, nastav URL a kľúč zariadenia.',
'12. Over časový limit, plnú/prázdnu nádrž, únik, stratu Wi-Fi, reštart servera a návrat hlavného napájania.',
]
for i,t in enumerate(steps):line(245-i*13,t,10)
line(70,'Bezpečné napätia sú iba DC vetvy modelu. Notebook a Wi-Fi router zostanú počas ukážky zapnuté.')
line(58,'Aktuálny kusovník: docs/KOMPONENTY.md; popis celého systému a AI: docs/AKO-TO-FUNGUJE.md.')
line(46,'Dĺžky hadičiek, priemery otvorov nádob a držiaky elektroniky dokonči až podľa fyzických dielov.')
pageend(6);c.save()
# A local index served by FastAPI /stavba/. No cloud or CDN resources.
(OUT/'index.html').write_text('''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Stavba smart domu</title><style>body{font:17px system-ui;max-width:1050px;margin:35px auto;padding:20px;background:#eef2f7;color:#182839}a{color:#174c92}img{width:100%;border-radius:12px}li{margin:12px 0}code{background:#dce5ef;padding:4px}</style><h1>Stavebné podklady smart domu</h1><p>Celé steny, odnímateľná strecha v jednom kuse, bez nábytku. Rozmery v milimetroch.</p><ul><li><a href="STAVEBNY-NAVOD.pdf">Stavebný návod PDF · A3</a></li><li><a href="3d/dom.blend">Editovateľný Blender model</a> · <a href="3d/dom.glb">3D GLB model</a></li><li><a href="vykresy/podorys.svg">Pôdorys s osadením</a> · <a href="rezaci-plan.csv">Rezací plán CSV</a></li><li><a href="dlzky-vodicov.csv">Dĺžky vodičov CSV</a> · <a href="hadicky.csv">Dĺžky hadičiek CSV</a></li></ul><p>SVG šablóny sú v priečinku <code>vykresy/</code>, každý diel má vlastný súbor Pxx-1ku1.svg. Tlač na 100 %, over kontrolnú mierku 100 mm. PDF je prehľad, nie šablóna 1:1.</p><img src="nahlady/dom-zatvoreny.jpg" alt="Zatvorený drevený dom"><img src="nahlady/dom-strecha-odlozena.jpg" alt="Dom so strechou odloženou, bez nábytku"><p>Aktívny 3D prehliadač je v aplikácii na karte 3D model a stavba.</p></html>''')
print('Generated cutting list, wire list, SVGs and A3 PDF.')
