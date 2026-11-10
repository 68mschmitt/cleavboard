#!/usr/bin/env python3
"""Isolated Cleaver-Embedded generator; writes only inside its own project.
Requires KiCad 10 pcbnew. --placement resets routing; --route restores archive.
"""
from pathlib import Path
import argparse,csv,json,math,re,subprocess,uuid
import xml.etree.ElementTree as ET
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
NAME='Cleaver-Embedded'
REVISION='embedded-0.2'
LIB=ROOT/(NAME+'.pretty')
DATA=json.loads((ROOT/'source/legacy-data.json').read_text())
W,H=452.4375,147.6375
def ident(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'cleaver:embedded-0.1:'+s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def mm(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def xy(v):return pcbnew.ToMM(v.x),pcbnew.ToMM(v.y)
MCU={1:'IOVDD',10:'IOVDD',19:'TESTEN',20:'XIN',21:'XOUT',22:'IOVDD',23:'DVDD',24:'SWCLK',25:'SWDIO',26:'RUN',33:'IOVDD',42:'IOVDD',43:'ADC_AVDD',44:'VREG_VIN',45:'VREG_VOUT',46:'USB_DM',47:'USB_DP',48:'USB_VDD',49:'IOVDD',50:'DVDD',51:'QSPI_SD3',52:'QSPI_SCLK',53:'QSPI_SD0',54:'QSPI_SD2',55:'QSPI_SD1',56:'QSPI_SS',57:'GND'}
for start,pins in [(0,range(2,10)),(8,range(11,19)),(16,range(27,33)),(22,range(34,42))]:MCU.update({p:'GP'+str(start+i) for i,p in enumerate(pins)})
def kinds():
    passive=lambda names:{str(n):(name,'passive') for n,name in names.items()}
    two=passive({1:'1',2:'2'})
    result={k:two for k in ['R_0805','C_0805','C_0805_Controller','PTC_1206','C_Radial8','R_0402','C_0402','Button']}
    result.update(MX=passive({1:'ROW',2:'KEY'}),D_SOD123=passive({1:'K',2:'A'}),TestPad=passive({1:'TEST'}),
      MINI_E={'1':('GND','power_in'),'2':('DIN','input'),'3':('VDD','power_in'),'4':('DOUT','output')},
      LV1T125={'1':('OE_N','input'),'2':('A','input'),'3':('GND','power_in'),'4':('Y','tri_state'),'5':('VCC','power_in')},
      TPS2553={'1':('IN','power_in'),'2':('GND','power_in'),'3':('EN','input'),'4':('FAULT_N','open_collector'),'5':('ILIM','passive'),'6':('OUT','power_out')},
      AP2112={'1':('VIN','power_in'),'2':('GND','power_in'),'3':('EN','input'),'4':('NC','no_connect'),'5':('VOUT','power_out')},
      Flash={'1':('CS_N','input'),'2':('IO1','bidirectional'),'3':('IO2','bidirectional'),'4':('GND','power_in'),'5':('IO0','bidirectional'),'6':('CLK','input'),'7':('IO3','bidirectional'),'8':('VCC','power_in')},
      Crystal=passive({1:'XTAL1',2:'GND',3:'XTAL2',4:'GND'}),
      USBLC6=passive({1:'IO1',2:'GND',3:'IO2',4:'IO2',5:'VBUS',6:'IO1'}),PowerFlag={'1':('PWR_FLAG','power_out')})
    result['RP2040']={str(n):(name,'power_in' if name in ['IOVDD','DVDD','GND','VREG_VIN','ADC_AVDD','USB_VDD'] else 'power_out' if name=='VREG_VOUT' else 'input' if name in ['XIN','TESTEN','RUN','SWCLK'] else 'output' if name in ['XOUT','QSPI_SCLK'] else 'bidirectional') for n,name in sorted(MCU.items())}
    result['USB_C']=passive({p:('VBUS' if p in ['A4','A9','B4','B9'] else 'GND' if p in ['A1','A12','B1','B12','S1'] else 'D+' if p in ['A6','B6'] else 'D-' if p in ['A7','B7'] else p) for p in ['A1','A4','A5','A6','A7','A8','A9','A12','B1','B4','B5','B6','B7','B8','B9','B12','S1']})
    return result
KINDS=kinds()
FP={'MX':'Kailh_socket_MX','RP2040':'RP2040_QFN56_EP3.2','USB_C':'USB_C_Receptacle_HRO_TYPE-C-31-M-12','AP2112':'SOT-23-5','Flash':'SOIC-8W_5.3x5.3mm_P1.27mm','Crystal':'Crystal_SMD_3225-4Pin_3.2x2.5mm','USBLC6':'USBLC6-2SC6_SOT23-6'}
def parts():
    out=[dict(p) for p in DATA['parts'] if p['ref'] not in ['U1','TP1']]
    def add(ref,kind,value,x,y,pins,back=True,angle=0):out.append(dict(ref=ref,kind=kind,value=value,x=x,y=y,pins={str(n):v for n,v in pins.items()},back=back,angle=angle))
    nets={n:None for n in MCU}
    for n,name in MCU.items():
        if name in ['IOVDD','ADC_AVDD','USB_VDD','VREG_VIN']:nets[n]='3V3'
        elif name in ['DVDD','VREG_VOUT']:nets[n]='1V1'
        elif name in ['GND','TESTEN']:nets[n]='GND'
        elif name.startswith('GP'):
            g=int(name[2:]);nets[n]=f'ROW{g}' if g<8 else f'COL{g-8:02d}' if g<23 else 'COL15' if g==26 else 'RGB_DATA' if g==27 else 'LED_EN' if g==28 else None
        else:nets[n]=name
    add('U1','RP2040','RP2040',421,13,nets,angle=-90)
    add('U4','Flash','W25Q32JVSSIQ 4MB',433,5,{1:'QSPI_SS',2:'QSPI_SD1',3:'QSPI_SD2',4:'GND',5:'QSPI_SD0',6:'QSPI_SCLK',7:'QSPI_SD3',8:'3V3'})
    add('U5','AP2112','AP2112K-3.3TRG1',439,21,{1:'RAW_USB_5V',2:'GND',3:'RAW_USB_5V',4:None,5:'3V3'})
    usb={p:('RAW_USB_5V' if name=='VBUS' else 'GND' if name=='GND' else 'USB_P' if name=='D+' else 'USB_N' if name=='D-' else 'CC1' if p=='A5' else 'CC2' if p=='B5' else None) for p,(name,typ) in KINDS['USB_C'].items()}
    add('J1','USB_C','HRO TYPE-C-31-M-12',449,13,usb,angle=90)
    add('U6','USBLC6','USBLC6-2SC6',438.5,13,{1:'USB_P',2:'GND',3:'USB_N',4:'USB_N',5:'RAW_USB_5V',6:'USB_P'})
    add('Y1','Crystal','ABM8-272-T3 12MHz',412,13,{1:'XIN',2:'GND',3:'XTAL_OUT',4:'GND'})
    for ref,value,x,y,a,b,angle in [('R10','27R 1%',426.5,14.4,'USB_DP','USB_P',0),('R11','27R 1%',426.5,15.6,'USB_DM','USB_N',0),('R12','5.1k 1%',442,8,'CC1','GND',0),('R13','5.1k 1%',442,18,'CC2','GND',0),('R14','1k 1%',415,13,'XOUT','XTAL_OUT',90),('R15','1k 1%',429,9,'QSPI_SS','BOOT_SW',0),('R16','10k 1%',429,7.5,'QSPI_SS','3V3',0),('R17','10k 1%',413,20,'RUN','3V3',0)]:add(ref,'R_0402',value,x,y,{1:a,2:b},angle=angle)
    add('BTN1','Button','PTS636 SK25 SMTR LFS BOOTSEL',405,6,{1:'BOOT_SW',2:'GND'})
    add('BTN2','Button','PTS636 SK25 SMTR LFS RESET',405,20,{1:'RUN',2:'GND'})
    add('C10','C_0402','15pF C0G 50V',409,11,{1:'XIN',2:'GND'})
    add('C11','C_0402','15pF C0G 50V',415,16,{1:'XTAL_OUT',2:'GND'})
    add('C12','C_0805','1uF X7R 50V',439,24,{1:'RAW_USB_5V',2:'GND'})
    add('C13','C_0805','1uF X7R 50V',439,18,{1:'3V3',2:'GND'})
    add('C14','C_0402','100nF X7R 16V',436,2,{1:'3V3',2:'GND'})
    add('C15','C_0402','100nF X7R 16V',440,10.5,{1:'RAW_USB_5V',2:'GND'})
    # One capacitor per supply pin, reverse-side near that pin.
    caps=[(1,418.4,9.6,'3V3'),(10,422,9.6,'3V3'),(22,417.6,13.2,'3V3'),(33,420,16.4,'3V3'),(42,423.6,16.4,'3V3'),(49,424.4,12.8,'3V3'),(43,424.4,15.2,'3V3'),(48,424.4,14,'3V3'),(23,417.6,14.4,'1V1'),(50,424.4,11.6,'1V1'),(44,426.8,15.2,'3V3'),(45,426.8,14,'1V1')]
    for i,(pin,x,y,net) in enumerate(caps,20):add(f'C{i}','C_0402',('1uF X5R 10V' if pin in [44,45] else '100nF X7R 16V'),x,y,{1:net,2:'GND'},back=True)
    for i,(net,x,y) in enumerate([('SWCLK',410,24),('SWDIO',413,24),('GND',416,24),('3V3',419,24),('1V1',422,24),('RUN',425,24)],10):add(f'TP{i}','TestPad',net,x,y,{1:net},back=True)
    # Single reflow side: coordinate values are in the normal top-view board frame.
    # Flip TOP_BOTTOM reflects local Y, retaining J1's right-facing mouth.
    placement={
        'U1':(428,11,-90),'U4':(435,20,90),'U5':(443,22,0),
        'U6':(441.5,12.7,0),'J1':(449,13,90),'Y1':(419.8,11.7,180),
        'R10':(433.2,10.3,0),'R11':(433.2,9.3,0),
        'R12':(443.2,7,0),'R13':(442.5,18.4,0),
        'R14':(422,9.3,180),'R15':(418,20,0),'R16':(431,18,90),
        'R17':(417,21,0),'BTN1':(405,5,0),'BTN2':(405,20,0),
        'C10':(420.5,14.5,90),'C11':(416.6,10.85,180),
        'C12':(447,23,0),'C13':(439.8,24.8,0),'C14':(430.5,23.7,0),'C15':(440,15.8,0),
        'C20':(430.6,16,90),'C21':(427,16,90),
        'C22':(423,10.8,180),'C28':(423,8.3,180),
        'C23':(427,6,-90),'C24':(430.6,6,-90),
        'C26':(433,7.3,0),'C30':(435,7.3,0),'C31':(433,8.3,0),
        'C27':(433,11.4,0),'C25':(435,11.4,0),'C29':(435,12.4,0),
    }
    for p in out:
        if p['ref'] in placement:p['x'],p['y'],p['angle']=placement[p['ref']]
        if p['ref'] in ['C12','C13']:p['kind']='C_0805_Controller'
    return out
def footprint(name,pads,body):
    x,y=body
    cx,cy={'RP2040_QFN56_EP3.2':(3.95,3.95),'Button':(4.65,2.0)}.get(name,(.925,.45))
    return f'''(footprint {q(name)} (layer F.Cu) (attr smd)
      (fp_text reference REF** (at 0 {-y-1}) (layer F.SilkS) (effects (font (size .8 .8) (thickness .12))))
      (fp_text value {q(name)} (at 0 {y+1}) (layer F.Fab) (effects (font (size .8 .8) (thickness .12))))
      (fp_rect (start {-x} {-y}) (end {x} {y}) (layer F.Fab) (width .1))
      (fp_rect (start {-cx} {-cy}) (end {cx} {cy}) (layer F.CrtYd) (width .05)) {pads})\n'''
def smd(n,x,y,w,h,layers='F.Cu F.Paste F.Mask'):return f'(pad {q(n)} smd rect (at {x} {y}) (size {w} {h}) (layers {layers}))'
def libraries():
    for fn in ['USB_C_Receptacle_HRO_TYPE-C-31-M-12','SOT-23-5','SOIC-8W_5.3x5.3mm_P1.27mm','Crystal_SMD_3225-4Pin_3.2x2.5mm']:
        text=(ROOT/'references'/f'{fn}.kicad_mod').read_text();text=re.sub(r'\s*\(model .*?\n  \)','',text,flags=re.S)
        if fn.startswith('USB_C'):text=text.replace('F.SilkS','F.Fab')
        (LIB/f'{fn}.kicad_mod').write_text(text)
    for kind in ['R_0402','C_0402']:(LIB/f'{kind}.kicad_mod').write_text(footprint(kind,smd(1,-.5,0,.55,.6)+smd(2,.5,0,.55,.6),(.5,.25)))
    pads=[]
    for i in range(14):
        d=round(-2.6+i*.4,4)
        for n,x,y,w,h in [(1+i,-3.45,d,.7,.2),(15+i,d,3.45,.2,.7),(29+i,3.45,-d,.7,.2),(43+i,-d,-3.45,.2,.7)]:pads.append(smd(n,x,y,w,h))
    pads.append(smd(57,0,0,3.2,3.2,'F.Cu F.Mask'))
    for x in [-.8,.8]:
        for y in [-.8,.8]:pads.append(smd('',x,y,1.25,1.25,'F.Paste'))
    (LIB/'RP2040_QFN56_EP3.2.kicad_mod').write_text(footprint('RP2040_QFN56_EP3.2','\n'.join(pads),(3.5,3.5)))
    # PTS636 SK25 gull-wing, datasheet p3: 9 outer / 6.5 inner, 2 x 1 tall.
    (LIB/'Button.kicad_mod').write_text(footprint('Button',smd(1,-3.875,0,1.25,1)+smd(2,3.875,0,1.25,1),(3.05,1.85)))
    esd=(LIB/'TPS2553.kicad_mod').read_text().replace('(module TPS2553 ','(module USBLC6-2SC6_SOT23-6 ',1)
    end=esd.rfind(')');esd=esd[:end]+'(fp_rect (start -1.95 -1.6) (end 1.95 1.6) (layer F.CrtYd) (width .05))\n'+esd[end:]
    (LIB/'USBLC6-2SC6_SOT23-6.kicad_mod').write_text(esd)
    cap=(LIB/'C_0805.kicad_mod').read_text().replace('(module C_0805 ','(module C_0805_Controller ',1)
    end=cap.rfind(')');cap=cap[:end]+'(fp_rect (start -1.75 -0.95) (end 1.75 .95) (layer F.CrtYd) (width .05))\n'+cap[end:]
    (LIB/'C_0805_Controller.kicad_mod').write_text(cap)
    for prefix,typ,uri in [('fp','KiCad',NAME+'.pretty'),('sym','KiCad',NAME+'.kicad_sym')]:
        (ROOT/(prefix+'-lib-table')).write_text(f'({prefix}_lib_table (lib (name "{NAME}") (type "{typ}") (uri "${{KIPRJMOD}}/{uri}") (options "") (descr "Isolated local library")))\n')
def pin_positions(kind):
    pins=list(KINDS[kind]);half=math.ceil(len(pins)/2);width=22.86 if kind=='RP2040' else 12.7 if len(pins)>8 else 7.62 if len(pins)>2 else 5.08
    return [(n,-width if i<half else width,round(((half-1)/2-(i%half))*2.54,3),0 if i<half else 180) for i,n in enumerate(pins)]
def symbol(kind,qualified=False):
    width=abs(pin_positions(kind)[0][1])-2.54;height=max(2.54,max(abs(y) for n,x,y,a in pin_positions(kind))+1.27)
    pins=''.join(f'(pin {KINDS[kind][n][1]} line (at {x} {y} {a}) (length 2.54) (name {q(KINDS[kind][n][0])} (effects (font (size .8 .8)))) (number {q(n)} (effects (font (size .8 .8)))))' for n,x,y,a in pin_positions(kind))
    def line(points):return '(polyline (pts '+''.join(f'(xy {x} {y})' for x,y in points)+') (stroke (width .15)) (fill (type none)))'
    graphic=f'(rectangle (start {-width} {height}) (end {width} {-height}) (stroke (width .15)) (fill (type background)))'
    if kind.startswith('R_') or kind=='PTC_1206':graphic='(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width .15)) (fill (type none)))'
    elif kind.startswith('C_'):graphic=line([(-2.54,0),(-.6,0)])+line([(-.6,-2),(-.6,2)])+line([(.6,-2),(.6,2)])+line([(.6,0),(2.54,0)])
    elif kind=='D_SOD123':graphic=line([(-2.54,0),(-1.5,0)])+line([(-1.5,-1.5),(-1.5,1.5)])+line([(-1.5,0),(1.5,1.5),(1.5,-1.5),(-1.5,0)])+line([(1.5,0),(2.54,0)])
    elif kind in ['MX','Button']:graphic=line([(-2.54,0),(2.54,1.27)])+'(circle (center -2.54 0) (radius .4) (stroke (width .15)) (fill (type none))) (circle (center 2.54 0) (radius .4) (stroke (width .15)) (fill (type none)))'
    return f'''(symbol {q(NAME+':'+kind if qualified else kind)} (pin_names (offset .5)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 0 0) (effects (font (size 1 1)))) (property "Value" {q(kind)} (at 0 0 0) (effects (font (size 1 1))))
      (property "Footprint" {q('' if kind=='PowerFlag' else NAME+':'+FP.get(kind,kind))} (at 0 0 0) (effects (font (size 1 1)) hide))
      (symbol {q(kind+'_0_1')} {graphic}) (symbol {q(kind+'_1_1')} {pins}))'''
def schematic(parts):
    body=[];instances=[];index=0
    layout={'U1':(65,590)}
    for i in range(12):layout[f'C{i+20}']=(145+(i%2)*65,550+(i//2)*25.4)
    for i in range(6):layout[f'TP{i+10}']=(40+i*42,715)
    groups=[(350,['U4','R16','C14','Y1','R14','C10','C11','R15','BTN1','R17','BTN2']),
            (650,['J1','U6','U5','R12','R10','C12','R13','R11','C13','C15','#FLG1','#FLG2','#FLG3']),
            (950,['F1','U3','U2','C1','R4','C3','C2','R2','R1','C5','R3','TP2','TP3','TP4','TP5','TP6'])]
    for origin,refs in groups:
        for i,ref in enumerate(refs):layout[ref]=(origin+(i%3)*70,555+(i//3)*32)
    allparts=parts+[dict(ref=f'#FLG{i}',kind='PowerFlag',value='PWR_FLAG',pins={'1':n}) for i,n in enumerate(['GND','RAW_USB_5V','FUSED_5V'],1)]
    keys={k['ref']:i for i,k in enumerate(DATA['keys'])};leds={k['led_ref']:i for i,k in enumerate(DATA['leds'])};caps={k['cap_ref']:i for i,k in enumerate(DATA['leds'])}
    for p in allparts:
        ref,kind=p['ref'],p['kind'];positions=pin_positions(kind)
        if ref in keys or (ref.startswith('D') and 'SW'+ref[1:] in keys):
            i=keys.get(ref,keys.get('SW'+ref[1:]));row,col=divmod(i,16);x,y=25+col*35.56+(15.24 if kind=='D_SOD123' else 0),50+row*27.94
        elif ref in leds or ref in caps:
            i=leds.get(ref,caps.get(ref));row,col=divmod(i,8);x,y=640+col*63.5+(30.48 if ref in caps else 0),50+row*30.48
        else:x,y=layout[ref]
        x,y=round(x/1.27)*1.27,round(y/1.27)*1.27;height=max(abs(py) for n,px,py,a in positions)+5.08
        fp='' if kind=='PowerFlag' else NAME+':'+FP.get(kind,kind);cid=ident(ref);on='no' if kind=='PowerFlag' else 'yes'
        body.append(f'''(symbol (lib_id {q(NAME+':'+kind)}) (at {x} {y} 0) (unit 1) (in_bom {on}) (on_board {on}) (dnp no) (uuid {cid})
          (property "Reference" {q(ref)} (at {x} {y-height} 0) (effects (font (size .8 .8)))) (property "Value" {q(p['value'])} (at {x} {y+height} 0) (effects (font (size .8 .8))))
          (property "Footprint" {q(fp)} (at {x} {y} 0) (effects (font (size 1 1)) hide)) {' '.join(f'(pin {q(n)} (uuid {ident(ref+":"+n)}))' for n in KINDS[kind])})''')
        instances.append(f'(path "/{cid}" (reference {q(ref)}) (unit 1) (value {q(p["value"])}) (footprint {q(fp)}))')
        for n,px,py,a in positions:
            nx,ny=round(x+px,4),round(y-py,4);net=p['pins'].get(n)
            if net is None:body.append(f'(no_connect (at {nx} {ny}) (uuid {ident(ref+":nc:"+n)}))')
            else:body.append(f'(label {q(net)} (at {nx} {ny} {180 if px<0 else 0}) (effects (font (size .8 .8)) (justify {"right" if px<0 else "left"} bottom)) (uuid {ident(ref+":net:"+n)}))')
    used=sorted({p['kind'] for p in allparts})
    text=f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0") (uuid {ident('root')}) (paper "User" 1189 1189)
      (title_block (title "Cleaver-Embedded / bare RP2040 / USB-C") (date "2026-11-09") (rev "{REVISION}")) (lib_symbols {' '.join(symbol(k,True) for k in used)})
      (text "117 KEYS / ROW2COL 8x16 / 117 SK6812MINI-E / RP2040 QFN56 / USB2 DEVICE" (at 25 20 0) (effects (font (size 2 2)) (justify left)))
      (text "USB-C VBUS -> AP2112 3V3 and F1 -> TPS2553 LED branch. 75k ILIM: ~353mA. RGB cap 8/255. No VBUS wire." (at 25 30 0) (effects (font (size 1.2 1.2)) (justify left)))
      (text "RP2040 / DECOUPLING / SWD" (at 25 520 0) (effects (font (size 2 2)) (justify left)))
      (text "FLASH / CLOCK / BOOT / RESET" (at 325 520 0) (effects (font (size 2 2)) (justify left)))
      (text "USB-C / ESD / 3V3 REGULATOR" (at 625 520 0) (effects (font (size 2 2)) (justify left)))
      (text "PROTECTED LED POWER / BUFFER" (at 925 520 0) (effects (font (size 2 2)) (justify left)))
      {' '.join(body)} (sheet_instances (path "/" (page "1"))) (symbol_instances {' '.join(instances)}) (embedded_fonts no))\n'''
    (ROOT/(NAME+'.kicad_sch')).write_text(text);(ROOT/(NAME+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n'+'\n'.join(symbol(k) for k in used)+')\n')
    subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(ROOT/'validation/netlist.xml'),str(ROOT/(NAME+'.kicad_sch'))],check=True)
    root=ET.parse(ROOT/'validation/netlist.xml').getroot();return {(p.get('ref'),p.get('pin')):n.get('name') for n in root.findall('./nets/net') for p in n.findall('node')}
def track(board,net,a,b,layer=pcbnew.F_Cu,width=.15):
    t=pcbnew.PCB_TRACK(board);t.SetStart(mm(*a));t.SetEnd(mm(*b));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));t.SetNet(board.FindNet('/'+net));board.Add(t);return t
def via(board,net,x,y):
    v=pcbnew.PCB_VIA(board);v.SetPosition(mm(x,y));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.3));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(board.FindNet('/'+net));board.Add(v);return v
def labels(b):
    texts=[(f'CLEAVER-EMBEDDED | {REVISION} | BOTTOM SMT | RGB 8/255',46,144.9,False),('BOOTSEL',405,8,True),('RESET',405,23,True)]
    texts += [(label,x,22.5,True) for label,x in [('CK',410),('IO',413),('GND',416),('3V3',419),('1V1',422),('RUN',425)]]
    for text,x,y,back in texts:
        t=pcbnew.PCB_TEXT(b);t.SetText(text);t.SetPosition(mm(x,y));t.SetLayer(pcbnew.B_SilkS if back else pcbnew.F_SilkS);t.SetMirrored(back);t.SetTextSize(mm(.8,.8));t.SetTextThickness(pcbnew.FromMM(.12));b.Add(t)
def board(parts,nets,route=None):
    b=pcbnew.LoadBoard(str(ROOT/'source/legacy-base.kicad_pcb'))
    held_fps=list(b.GetFootprints())
    for fp in held_fps:
        if fp.GetReference() in ['U1','TP1']:b.Remove(fp)
    held_tracks=list(b.GetTracks())
    from shapely.geometry import LineString,box
    cut=box(399,-1,W+1,26)
    for t in held_tracks:
        if t.GetClass()=='PCB_VIA':
            x,y=xy(t.GetPosition())
            if x>399 and y<26:b.Remove(t)
            continue
        line=LineString([xy(t.GetStart()),xy(t.GetEnd())])
        if not line.intersects(cut):continue
        remains=line.difference(cut);b.Remove(t)
        for piece in list(remains.geoms) if hasattr(remains,'geoms') else [remains]:
            if piece.is_empty or piece.length<.01:continue
            new=t.Duplicate();new.SetStart(mm(*piece.coords[0]));new.SetEnd(mm(*piece.coords[-1]));b.Add(new)
    held_drawings=list(b.GetDrawings())
    for d in held_drawings:
        if d.GetClass()=='PCB_TEXT' and any(s in d.GetText() for s in ['TAP','rev0.4']):b.Remove(d)
    for name in sorted(set(nets.values())):
        if not b.FindNet(name):b.Add(pcbnew.NETINFO_ITEM(b,name))
    existing={f.GetReference():f for f in b.GetFootprints()}
    for p in parts:
        ref,kind=p['ref'],p['kind'];fname=FP.get(kind,kind)
        if ref in existing:fp=existing[ref]
        else:
            fp=pcbnew.FootprintLoad(str(LIB),fname);fp.SetReference(ref);fp.SetValue(p['value']);fp.SetPosition(mm(p['x'],p['y']));fp.SetOrientationDegrees(p['angle']);b.Add(fp)
            if p['back']:fp.Flip(fp.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
            # Connector overhang is intentional; no silkscreen across edge.
            if ref=='J1':
                for shape in fp.GraphicalItems():
                    if shape.GetLayer()==pcbnew.F_SilkS:shape.SetLayer(pcbnew.F_Fab)
        fp.SetFPID(pcbnew.LIB_ID(NAME,fname));fp.SetPath(pcbnew.KIID_PATH('/'+ident(ref)))
        for pad in fp.Pads():
            name=nets.get((ref,str(pad.GetNumber())))
            if name:pad.SetNet(b.FindNet(name))
    for fp in b.GetFootprints():fp.SetFPID(pcbnew.LIB_ID(NAME,fp.GetFPID().GetLibItemName()))
    b.GetTitleBlock().SetTitle('Cleaver-Embedded / RP2040 / USB-C / 117 keys');b.GetTitleBlock().SetRevision(REVISION);b.GetTitleBlock().SetDate('2026-11-09')
    # Ordinary masked vias outside the exposed pad and paste: no via-in-pad.
    for x,y in [(426,10.8),(425.8,11.4),(430.2,10.2),(430.2,10.8)]:
        v=via(b,'GND',x,y);v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
        track(b,'GND',(428,y),(x,y),pcbnew.B_Cu,width=.4)
    # Escape internal GPIO pins under the package before routing other nets.
    # Alternate two radial rows; keep corners free for adjacent-side escapes.
    u1=next(f for f in b.GetFootprints() if f.GetReference()=='U1')
    for pad in u1.Pads():
        n=pad.GetNumber()
        if not n or n=='57' or not pad.GetNetname() or pad.GetNetname().startswith('unconnected-'):continue
        i=(int(n)-1)%14
        if i<2 or i>11:continue
        x,y=xy(pad.GetPosition());dx,dy=x-428,y-11
        radius=2.15 if i%2 else 2.8
        if int(n) in [20,21,22,43,44,45,46,47,48,49,50,51,52,53,54,55,56]:continue
        vx,vy=(428+math.copysign(radius,dx),y) if abs(dx)>abs(dy) else (x,11+math.copysign(radius,dy))
        track(b,pad.GetNetname().lstrip('/'),(x,y),(vx,vy),pcbnew.B_Cu,width=.127)
        v=via(b,pad.GetNetname().lstrip('/'),vx,vy);v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2))
    from critical import route_critical
    route_critical(b)
    z=pcbnew.ZONE(b);z.SetLayer(pcbnew.F_Cu);z.SetNet(b.FindNet('/GND'));z.SetAssignedPriority(10);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    poly=z.Outline();poly.NewOutline()
    for x,y in [(399,.6),(W-.6,.6),(W-.6,25.5),(399,25.5)]:poly.Append(*mm(x,y))
    b.Add(z)
    # Adjacent ground reference; route.py reserves USB/clock ground corridors.
    inner=z.Duplicate(False);inner.SetLayer(pcbnew.In2_Cu);b.Add(inner)
    logo=pcbnew.FootprintLoad(str(LIB),'TavianaTactical_34mm')
    logo.SetFPID(pcbnew.LIB_ID(NAME,'TavianaTactical_34mm'))
    logo.SetReference('LOGO1');logo.SetPosition(mm(199,122));b.Add(logo)
    logo.SetLocked(True)
    labels(b)
    for zone in b.Zones():
        if not zone.GetIsRuleArea():zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if route:
        held_route_tracks=list(b.GetTracks())
        for t in held_route_tracks:b.Remove(t)
        if not pcbnew.ImportSpecctraSES(b,str(route)):raise RuntimeError('Route import failed')
        options_path=ROOT/'routing/via-options.json'
        if options_path.exists():
            options={(o['x'],o['y'],o['net']):o for o in json.loads(options_path.read_text())}
            for t in b.GetTracks():
                if t.GetClass()!='PCB_VIA':continue
                o=options.get((t.GetPosition().x,t.GetPosition().y,t.GetNetname()))
                if o:t.SetFrontTentingMode(o['front']);t.SetBackTentingMode(o['back'])
    pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b);project();b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b);project()
    if not route:pcbnew.ExportSpecctraDSN(b,str(ROOT/'routing/placement.dsn'))
def project():
    p=ROOT/(NAME+'.kicad_pro');data=json.loads(p.read_text());data['meta']['filename']=NAME+'.kicad_pro'
    ds=data['board']['design_settings'];ds['rules'].update(min_track_width=.127,min_via_diameter=.4,min_through_hole_diameter=.2,min_hole_clearance=.2);ds['drc_exclusions']=[]
    for c in data['net_settings']['classes']:
        if c['name']=='Default':c.update(clearance=.127,track_width=.15,via_diameter=.5,via_drill=.3)
    p.write_text(json.dumps(data,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--placement',action='store_true');group.add_argument('--route',type=Path);args=parser.parse_args()
    if args.route and args.route.resolve().parent!=ROOT/'routing':parser.error('Route must be inside this project routing/')
    libraries();project();ps=parts();nets=schematic(ps);board(ps,nets,args.route);(ROOT/'source/components.json').write_text(json.dumps(ps,indent=2)+'\n')
    (ROOT/'manufacturing').mkdir(exist_ok=True)
    with (ROOT/'manufacturing/BOM.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['reference','value_or_MPN','footprint','x_mm','y_mm','side'])
        for p in ps:w.writerow([p['ref'],p['value'],NAME+':'+FP.get(p['kind'],p['kind']),p['x'],p['y'],'B' if p['back'] or p['kind']=='MX' else 'F'])
    print('Generated',len(ps),'parts;', 'route imported' if args.route else 'PLACEMENT REQUIRES ROUTING')
if __name__=='__main__':main()
