#!/usr/bin/env python3
"""Isolated white design. --placement deliberately resets routing.
Default rebuild imports archived complete copper; never touches other designs.
"""
from pathlib import Path
import argparse,json,math,re,subprocess,uuid
import xml.etree.ElementTree as ET
import pcbnew
from sourcing import SELECTED,fields
ROOT=Path(__file__).resolve().parents[1]
NAME='Cleaver-White'
LIB=ROOT/(NAME+'.pretty')
DATA=json.loads((ROOT/'source/layout.json').read_text())
W,H=452.4375,147.6375
def ident(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'cleaver:white-0.1:'+s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def mm(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def xy(v):return pcbnew.ToMM(v.x),pcbnew.ToMM(v.y)
FP={**{k:v['footprint'] for k,v in SELECTED.items()},'NMOS':'SOT-23'}
def parts():
    out=[dict(p,pins=dict(p['pins'])) for p in DATA['parts'] if p['kind'] in ['MX','D_SOD123','YD_RP2040']]
    for p in out:
        if p['kind']=='MX':p['key_label']=p['value'];p['value']=SELECTED['MX']['MPN']
    u=next(p for p in out if p['ref']=='U1');u['pins']['32']='BL_PWM';u['pins']['40']='MODULE_VOUT'
    def add(ref,kind,value,x,y,pins,back=True,angle=0):out.append(dict(ref=ref,kind=kind,value=value,x=x,y=y,pins={str(n):v for n,v in pins.items()},back=back,angle=angle))
    for i,k in enumerate(DATA['keys'],1):
        add(k['led_ref'],'WhiteLED',SELECTED['WhiteLED']['MPN'],k['x'],k['y']+5.08,{1:'LED_RETURN',2:f'ANODE{i:03d}'})
        add(f'RL{i:03d}','R_0805','3.9k 1%',k['x']+5.8,k['y']+5.08,{1:f'ANODE{i:03d}',2:'LED_5V'})
    add('F1','PTC_1206','1206L020YR 0.20A hold',393,4.5,{1:'MODULE_VOUT',2:'FUSED_5V'})
    add('U3','TPS2553','TPS2553DBVR',390,14,{1:'FUSED_5V',2:'GND',3:'LED_EN',4:None,5:'FUSED_5V',6:'LED_5V'})
    add('R2','R_0805','100k 1%',384,10,{1:'LED_EN',2:'GND'})
    add('C1','C_0805','1uF 50V X7R',394,8,{1:'FUSED_5V',2:'GND'})
    add('C2','C_0805','22uF 10V X5R',395,14,{1:'LED_5V',2:'GND'})
    add('Q1','NMOS','AO3400A',382,19,{1:'GATE',2:'GND',3:'LED_RETURN'})
    add('R1','R_0805','330R 1%',378,19,{1:'BL_PWM',2:'GATE'})
    add('R3','R_0805','100k 1%',382,23,{1:'GATE',2:'GND'})
    for ref,net,x in [('TP2','GND',410),('TP3','MODULE_VOUT',418),('TP4','LED_5V',426),('TP5','LED_EN',434),('TP6','LED_RETURN',402)]:add(ref,'TestPad',net,x,27,{1:net})
    return out
def pins():
    passive=lambda names:{str(n):(v,'passive') for n,v in names.items()}
    two=passive({1:'1',2:'2'})
    result={k:two for k in ['R_0805','C_0805','PTC_1206']}
    result.update(MX=passive({1:'ROW',2:'KEY'}),D_SOD123=passive({1:'K',2:'A'}),WhiteLED=passive({1:'K',2:'A'}),NMOS=passive({1:'G',2:'S',3:'D'}),TestPad=passive({1:'TEST'}),PowerFlag={'1':('PWR_FLAG','power_out')},TPS2553={'1':('IN','power_in'),'2':('GND','power_in'),'3':('EN','input'),'4':('FAULT_N','open_collector'),'5':('ILIM','passive'),'6':('OUT','power_out')})
    result['YD_RP2040']={n:(v,'power_in' if v in ['GND','VIN'] else 'power_out' if v in ['VOUT','3V3_OUT'] else 'input' if v=='RUN' else 'bidirectional') for n,v in DATA['module_pins'].items()}
    return result
PINS=pins()
def positions(kind):
    ns=list(PINS[kind]);half=math.ceil(len(ns)/2);width=25.4 if len(ns)>8 else 7.62 if len(ns)>2 else 5.08
    return [(n,-width if i<half else width,round(((half-1)/2-(i%half))*2.54,3),0 if i<half else 180) for i,n in enumerate(ns)]
def symbol(kind,qualified=False):
    pos=positions(kind);width=abs(pos[0][1])-2.54;height=max(2.54,max(abs(y) for n,x,y,a in pos)+1.27)
    p=''.join(f'(pin {PINS[kind][n][1]} line (at {x} {y} {a}) (length 2.54) (name {q(PINS[kind][n][0])} (effects (font (size .8 .8)))) (number {q(n)} (effects (font (size .8 .8)))))' for n,x,y,a in pos)
    def line(points):return '(polyline (pts '+''.join(f'(xy {x} {y})' for x,y in points)+') (stroke (width .15)) (fill (type none)))'
    graphic=f'(rectangle (start {-width} {height}) (end {width} {-height}) (stroke (width .15)) (fill (type background)))'
    if kind.startswith('R_') or kind=='PTC_1206':graphic='(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width .15)) (fill (type none)))'
    elif kind.startswith('C_'):graphic=line([(-2.54,0),(-.6,0)])+line([(-.6,-2),(-.6,2)])+line([(.6,-2),(.6,2)])+line([(.6,0),(2.54,0)])
    elif kind in ['D_SOD123','WhiteLED']:
        graphic=line([(-2.54,0),(-1.5,0)])+line([(-1.5,-1.5),(-1.5,1.5)])+line([(-1.5,0),(1.5,1.5),(1.5,-1.5),(-1.5,0)])+line([(1.5,0),(2.54,0)])
        if kind=='WhiteLED':graphic+=line([(0,2),(1,3),(.5,3)])+line([(1,1.8),(2,2.8),(1.5,2.8)])
    elif kind=='MX':graphic=line([(-2.54,0),(2.54,1.27)])
    return f'''(symbol {q(NAME+':'+kind if qualified else kind)} (pin_names (offset .5) {'hide' if len(pos)==2 else ''}) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 0 0) (effects (font (size 1 1)))) (property "Value" {q(kind)} (at 0 0 0) (effects (font (size 1 1))))
      (property "Footprint" {q('' if kind=='PowerFlag' else NAME+':'+FP.get(kind,kind))} (at 0 0 0) (effects (font (size 1 1)) hide))
      (symbol {q(kind+'_0_1')} {graphic}) (symbol {q(kind+'_1_1')} {p}))'''
def schematic(parts):
    body=[];instances=[];corner=0
    allparts=parts+[dict(ref=f'#FLG{i}',kind='PowerFlag',value='PWR_FLAG',pins={'1':n}) for i,n in enumerate(['GND','FUSED_5V'],1)]
    for part in allparts:
        ref,kind=part['ref'],part['kind'];pos=positions(kind)
        if kind in ['MX','D_SOD123']:
            i=int(re.sub(r'\D','',ref))-1;row,col=divmod(i,16);x,y=25+col*35.56,45+row*30.48+(12.7 if kind=='D_SOD123' else 0)
        elif kind=='WhiteLED' or ref.startswith('RL'):
            i=int(re.sub(r'\D','',ref))-1;row,col=divmod(i,8);x,y=640+col*66.04+(27.94 if ref.startswith('RL') else 0),45+row*30.48
        elif ref=='U1':x,y=65,380
        else:x,y=160+(corner%5)*80,340+(corner//5)*45.72;corner+=1
        x,y=round(x/1.27)*1.27,round(y/1.27)*1.27;height=max(abs(py) for n,px,py,a in pos)+5.08
        fp='' if kind=='PowerFlag' else NAME+':'+FP.get(kind,kind);cid=ident(ref);on='no' if kind=='PowerFlag' else 'yes'
        properties=''.join(f'(property {q(k)} {q(v)} (at {x} {y} 0) (effects (font (size 1 1)) hide))' for k,v in fields(part).items())
        body.append(f'''(symbol (lib_id {q(NAME+':'+kind)}) (at {x} {y} 0) (unit 1) (in_bom {on}) (on_board {on}) (dnp no) (uuid {cid})
          (property "Reference" {q(ref)} (at {x} {y-height} 0) (effects (font (size .8 .8)))) (property "Value" {q(part['value'])} (at {x} {y+height} 0) (effects (font (size .8 .8))))
          (property "Footprint" {q(fp)} (at {x} {y} 0) (effects (font (size 1 1)) hide)) {properties} {' '.join(f'(pin {q(n)} (uuid {ident(ref+":"+n)}))' for n in PINS[kind])})''')
        instances.append(f'(path "/{cid}" (reference {q(ref)}) (unit 1) (value {q(part["value"])}) (footprint {q(fp)}))')
        for n,px,py,a in pos:
            nx,ny=round(x+px,4),round(y-py,4);net=part['pins'].get(n)
            if net is None:body.append(f'(no_connect (at {nx} {ny}) (uuid {ident(ref+":nc:"+n)}))')
            else:body.append(f'(label {q(net)} (at {nx} {ny} {180 if px<0 else 0}) (effects (font (size .8 .8)) (justify {"right" if px<0 else "left"} bottom)) (uuid {ident(ref+":net:"+n)}))')
    used=sorted({p['kind'] for p in allparts})
    text=f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0") (uuid {ident('root')}) (paper "User" 1189 594)
      (title_block (title "Cleaver-White / top YD-RP2040 / bottom SMT") (date "2026-11-10") (rev "white-0.1")) (lib_symbols {' '.join(symbol(k,True) for k in used)})
      (text "117 KEYS / 8x16 ROW2COL / ORIGINAL MATRIX" (at 20 20 0) (effects (font (size 2 2)) (justify left)))
      (text "117 REVERSE-MOUNT WHITE LEDs / ONE 3.9k RESISTOR PER LED" (at 625 20 0) (effects (font (size 2 2)) (justify left)))
      (text "TOP MODULE / PROTECTED HEADER POWER / BOTTOM SMD SUPPORT" (at 20 305 0) (effects (font (size 2 2)) (justify left)))
      (text "U1.40 Vout -> F1 -> U3 -> 117 resistor/LED branches -> Q1 -> GND. NO external power input. VIN / 3V3 unused." (at 20 485 0) (effects (font (size 1.2 1.2)) (justify left)))
      (text "U3 ILIM = IN: datasheet 50/75/100mA min/typ/max. GP28 EN default off. GP27 PWM -> 330R -> AO3400A gate, 100k pull-down." (at 20 493 0) (effects (font (size 1.2 1.2)) (justify left)))
      (text "Module BAT54C is shared by controller and LEDs: see POWER.md. USB configuration enables backlight; suspend disables it." (at 20 501 0) (effects (font (size 1.2 1.2)) (justify left)))
      {' '.join(body)} (sheet_instances (path "/" (page "1"))) (symbol_instances {' '.join(instances)}) (embedded_fonts no))\n'''
    (ROOT/(NAME+'.kicad_sch')).write_text(text)
    (ROOT/(NAME+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n'+'\n'.join(symbol(k) for k in used)+')\n')
    subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(ROOT/'validation/netlist.xml'),str(ROOT/(NAME+'.kicad_sch'))],check=True)
    root=ET.parse(ROOT/'validation/netlist.xml').getroot();return {(p.get('ref'),p.get('pin')):n.get('name') for n in root.findall('./nets/net') for p in n.findall('node')}
def libraries():
    # Same measured MX holes/pads; use an exact purchasing identity in KiCad.
    from models_3d import without_models
    socket=without_models((LIB/'Kailh_socket_MX.kicad_mod').read_text())
    socket=socket.replace('Kailh_socket_MX',FP['MX']).replace('MX-style keyswitch with Kailh socket mount','HanElectricity CPG151101S11-16 C41430893; underside socket, retained MX holes/pads')
    (LIB/(FP['MX']+'.kicad_mod')).write_text(socket)
    for prefix in ['fp','sym']:
        uri=NAME+('.pretty' if prefix=='fp' else '.kicad_sym')
        (ROOT/(prefix+'-lib-table')).write_text(f'({prefix}_lib_table (lib (name "{NAME}") (type "KiCad") (uri "${{KIPRJMOD}}/{uri}") (options "") (descr "Isolated white design")))\n')
    def smd(n,x,y,w,h):return f'(pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers F.Cu F.Mask F.Paste))'
    led=f'''(footprint "{FP['WhiteLED']}" (layer F.Cu) (attr smd)
      (descr "BrtLed BL-HZ333H-L21-TRE C5123487 reverse mount; K=1 A=2; custom aperture lands, see MECHANICAL.md")
      (fp_text reference "REF**" (at 0 -2.1) (layer F.SilkS) (effects (font (size .8 .8) (thickness .12))))
      (fp_text value "BL-HZ333H-L21-TRE" (at 0 2.2) (layer F.Fab) (effects (font (size .8 .8) (thickness .12))))
      (fp_rect (start -1.6 -.8) (end 1.6 .8) (layer F.Fab) (width .1))
      (fp_rect (start -2.8 -1.4) (end 2.8 1.4) (layer F.CrtYd) (width .05))
      (fp_line (start -2.7 -1.15) (end -1.3 -1.15) (layer F.SilkS) (width .12))
      {smd(1,-1.875,0,1.35,1.6)} {smd(2,1.875,0,1.35,1.6)}
      (fp_rect (start -1.05 -1.15) (end 1.05 1.15) (layer Edge.Cuts) (width .05)))'''
    (LIB/(FP['WhiteLED']+'.kicad_mod')).write_text(led+'\n')
    mos=f'''(footprint "SOT-23" (layer F.Cu) (attr smd)
      (fp_text reference "REF**" (at 0 -2.5) (layer F.SilkS) (effects (font (size .8 .8) (thickness .12))))
      (fp_text value "AO3400A" (at 0 2.5) (layer F.Fab) (effects (font (size .8 .8) (thickness .12))))
      (fp_rect (start -.7 -1.5) (end .7 1.5) (layer F.Fab) (width .1))
      (fp_rect (start -2 -1.8) (end 2 1.8) (layer F.CrtYd) (width .05))
      {smd(1,-1.15,-.95,1.3,.6)} {smd(2,-1.15,.95,1.3,.6)} {smd(3,1.15,0,1.3,.6)})'''
    (LIB/'SOT-23.kicad_mod').write_text(mos+'\n')
def track(b,net,a,c,layer=pcbnew.B_Cu,width=.3):
    t=pcbnew.PCB_TRACK(b);t.SetStart(mm(*a));t.SetEnd(mm(*c));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));t.SetNet(b.FindNet('/'+net));b.Add(t)
def via(b,net,x,y):
    v=pcbnew.PCB_VIA(b);v.SetPosition(mm(x,y));v.SetWidth(pcbnew.FromMM(.6));v.SetDrill(pcbnew.FromMM(.3));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(b.FindNet('/'+net));v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED);b.Add(v)
def board(parts,nets,placement=False):
    b=pcbnew.LoadBoard(str(ROOT/'source/base-rev04.kicad_pcb'))
    keep={p['ref'] for p in parts if p['kind'] in ['MX','D_SOD123','YD_RP2040']}
    held=list(b.GetFootprints())
    for f in held:
        if f.GetReference() not in keep and not f.GetReference().startswith(('H','FID')):b.Remove(f)
    heldt=list(b.GetTracks())
    for t in heldt:
        if not t.GetNetname().startswith(('/ROW','/COL','/KEY')):b.Remove(t)
    heldz=list(b.Zones())
    for z in heldz:
        if not z.GetIsRuleArea():b.Remove(z)
    heldd=list(b.GetDrawings())
    for d in heldd:
        if d.GetClass()=='PCB_TEXT':b.Remove(d)
    for name in sorted(set(nets.values())):
        if not b.FindNet(name):b.Add(pcbnew.NETINFO_ITEM(b,name))
    existing={f.GetReference():f for f in b.GetFootprints()}
    for p in parts:
        ref,kind=p['ref'],p['kind'];fname=FP.get(kind,kind)
        if ref in existing:fp=existing[ref]
        else:
            fp=pcbnew.FootprintLoad(str(LIB),fname);fp.SetPosition(mm(p['x'],p['y']));fp.SetOrientationDegrees(p['angle']);b.Add(fp)
            if p['back']:fp.Flip(fp.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetReference(ref);fp.SetValue(p['value']);fp.SetFPID(pcbnew.LIB_ID(NAME,fname));fp.SetPath(pcbnew.KIID_PATH('/'+ident(ref)))
        for key,value in fields(p).items():
            fp.SetField(key,value);fp.GetField(key).SetVisible(False)
        if kind=='MX':fp.SetLibDescription('HanElectricity CPG151101S11-16 C41430893; underside socket, retained MX holes/pads')
        fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
        for pad in fp.Pads():
            name=nets.get((ref,str(pad.GetNumber())))
            pad.SetNet(b.FindNet(name) if name else b.FindNet(0))
    for fp in b.GetFootprints():
        fp.SetFPID(pcbnew.LIB_ID(NAME,fp.GetFPID().GetLibItemName()));fp.Models().clear()
    for k in DATA['keys']:
        x,y=k['x'],k['y']+5.08;i=int(k['ref'][2:]);net=f'ANODE{i:03d}'
        track(b,net,(x+1.875,y),(x+4.85,y));track(b,'LED_RETURN',(x-1.875,y),(x-3.3,y));via(b,'LED_RETURN',x-3.3,y)
        track(b,'LED_5V',(x+6.75,y),(x+7.9,y));via(b,'LED_5V',x+7.9,y)
    for layer,net in [(pcbnew.F_Cu,'LED_5V'),(pcbnew.In1_Cu,'GND'),(pcbnew.In2_Cu,'LED_RETURN')]:
        z=pcbnew.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/'+net));z.SetLocalClearance(pcbnew.FromMM(.2));z.SetMinThickness(pcbnew.FromMM(.2));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        poly=z.Outline();poly.NewOutline()
        for x,y in [(.6,.6),(W-.6,.6),(W-.6,H-.6),(.6,H-.6)]:poly.Append(*mm(x,y))
        b.Add(z)
    b.GetTitleBlock().SetTitle('Cleaver-White / top module / underside SMT');b.GetTitleBlock().SetRevision('white-0.1');b.GetTitleBlock().SetDate('2026-11-10');b.GetDesignSettings().SetAuxOrigin(mm(0,H))
    for text,x,y,back in [('CLEAVER WHITE 0.1 | 117 KEYS | TOP YD-RP2040 | BOTTOM SMT',50,144.8,False),('PIN40 VOUT ONLY - NO EXTERNAL POWER',425,25,True),('WHITE / 3.9k / 50-100mA LIMIT',379,28,True)]:
        t=pcbnew.PCB_TEXT(b);t.SetText(text);t.SetPosition(mm(x,y));t.SetLayer(pcbnew.B_SilkS if back else pcbnew.F_SilkS);t.SetMirrored(back);t.SetTextSize(mm(.8,.8));t.SetTextThickness(pcbnew.FromMM(.12));b.Add(t)
    from artwork import add as add_artwork
    add_artwork(b)
    if not placement:
        for t in list(b.GetTracks()):b.Remove(t)
        if not pcbnew.ImportSpecctraSES(b,str(ROOT/'source/complete.ses')):raise RuntimeError('Routing import failed')
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--placement',action='store_true');args=parser.parse_args()
    libraries();p=parts();(ROOT/'source/components.json').write_text(json.dumps(p,indent=2)+'\n');nets=schematic(p);board(p,nets,args.placement)
    from led_model import main as led_model
    led_model()
    from models_3d import main as attach_models
    attach_models()
if __name__=='__main__':main()
