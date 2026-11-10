#!/usr/bin/env python3
"""Check this isolated design, without modifying PCB or schematic."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
import xml.etree.ElementTree as ET
import pcbnew
from shapely.geometry import Point,LineString,box
ROOT=Path(__file__).resolve().parents[1]
NAME='Cleaver-Embedded'
def run(args):subprocess.run(['kicad-cli']+list(map(str,args)),check=True)
def main():
    report=ROOT/'validation';report.mkdir(exist_ok=True)
    sch=ROOT/(NAME+'.kicad_sch');pcb=ROOT/(NAME+'.kicad_pcb')
    run(['sch','export','netlist','--format','kicadxml','-o',report/'netlist.xml',sch])
    run(['sch','erc','--format','json','--severity-all','-o',report/'erc.json',sch])
    run(['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',report/'drc.json',pcb])
    board=pcbnew.LoadBoard(str(pcb));fps={f.GetReference():f for f in board.GetFootprints()}
    root=ET.parse(report/'netlist.xml').getroot()
    nets={(p.get('ref'),p.get('pin')):n.get('name') for n in root.findall('./nets/net') for p in n.findall('node')}
    issues=[]
    def require(ok,msg):
        if not ok:issues.append(msg)
    def net(ref,pin):return next(p.GetNetname().lstrip('/') for p in fps[ref].Pads() if p.GetNumber()==str(pin))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            key=(fp.GetReference(),p.GetNumber())
            if key in nets:require(p.GetNetname()==nets[key],f'Netlist/PCB mismatch {key}')
    require(fps['U1'].GetValue()=='RP2040','MCU value')
    require(len([p for p in fps['U1'].Pads() if p.GetNumber()])==57,'QFN56 + exposed ground pad')
    def bounds(item):
        bb=item.GetBoundingBox();return box(*[pcbnew.ToMM(v) for v in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]])
    top_smd=[];top_paste=[];bottom_smd=0
    for f in fps.values():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Paste):top_paste.append([f.GetReference(),p.GetNumber()])
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:
                if p.IsOnLayer(pcbnew.F_Cu):top_smd.append([f.GetReference(),p.GetNumber()])
                if p.IsOnLayer(pcbnew.B_Cu):bottom_smd+=1
    require(not top_smd,'All actual SMD copper is underside, including composite socket pads')
    require(not top_paste,'No front paste, including unnumbered QFN paste windows')
    ep=next(p for p in fps['U1'].Pads() if p.GetNumber()=='57');epgeom=bounds(ep)
    epvias=[]
    for t in board.GetTracks():
        if t.GetClass()!='PCB_VIA':continue
        pos=Point(pcbnew.ToMM(t.GetPosition().x),pcbnew.ToMM(t.GetPosition().y));distance=pos.distance(epgeom)
        require(distance>=pcbnew.ToMM(t.GetDrillValue())/2+.2-1e-6,'No drill within exposed pad/paste solder-wicking keepout')
        if t.GetNetname()=='/GND' and distance<.7:epvias.append(t)
    require(len(epvias)==4 and all(t.GetDrillValue()==pcbnew.FromMM(.3) for t in epvias),'Four ordinary 0.3mm ground drills outside exposed pad')
    paste=[p for p in fps['U1'].Pads() if not p.GetNumber() and p.IsOnLayer(pcbnew.B_Paste)]
    require(len(paste)==4 and all(p.GetSize().x==pcbnew.FromMM(1.25) and p.GetSize().y==pcbnew.FromMM(1.25) for p in paste),'Four 1.25mm bottom EP paste windows')
    controller=['U1','U4','U5','U6','J1','Y1','BTN1','BTN2']+[f'R{i}' for i in range(10,18)]+[f'C{i}' for i in list(range(10,16))+list(range(20,32))]
    courtyards={};bodies={}
    for ref in controller:
        f=fps[ref];require(f.GetLayer()==pcbnew.B_Cu,f'Bottom controller footprint {ref}')
        for layer,target in [(pcbnew.B_CrtYd,courtyards),(pcbnew.B_Fab,bodies)]:
            shapes=[s for s in f.GraphicalItems() if s.GetClass()=='PCB_SHAPE' and s.GetLayer()==layer]
            require(bool(shapes),f'Physical outline {ref} on {board.GetLayerName(layer)}')
            if shapes:
                boxes=[bounds(s).bounds for s in shapes];target[ref]=box(min(p[0] for p in boxes),min(p[1] for p in boxes),max(p[2] for p in boxes),max(p[3] for p in boxes))
    for name,shapes in [('courtyard',courtyards),('body',bodies)]:
        for i,a in enumerate(controller):
            for c in controller[i+1:]:
                if a in shapes and c in shapes:require(shapes[a].intersection(shapes[c]).area<1e-7,f'Same-side {name} clearance {a}/{c}')
    require(bodies['J1'].bounds[2]>452.4375 and bodies['J1'].bounds[0]>444,'USB mouth remains right-facing')
    for ref,pin in [('C20',1),('C21',10),('C22',22),('C23',33),('C24',42),('C25',48),('C26',43),('C27',49),('C28',23),('C29',50),('C30',44),('C31',45)]:
        p=next(p for p in fps['U1'].Pads() if p.GetNumber()==str(pin));a=p.GetPosition();c=fps[ref].GetPosition()
        require(((a.x-c.x)**2+(a.y-c.y)**2)**.5<pcbnew.FromMM(4),f'Adjacent decoupler {ref}/U1.{pin}')
    ground_vias=[t for t in board.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetname()=='/GND'];returns={}
    for ref in ['Y1']+[f'C{i}' for i in list(range(10,16))+list(range(20,32))]:
        for p in fps[ref].Pads():
            if p.GetNetname()!='/GND':continue
            a=p.GetPosition();distance=min(((a.x-v.GetPosition().x)**2+(a.y-v.GetPosition().y)**2)**.5/1e6 for v in ground_vias)
            returns[f'{ref}.{p.GetNumber()}']=round(distance,4);require(distance<=1.501,f'Local decoupler/crystal ground via {ref}.{p.GetNumber()}')
    (report/'local-ground.json').write_text(json.dumps({'nearest_ground_via_mm':returns,'maximum_mm':max(returns.values()),'limit_mm':1.5,'pass':all(d<=1.501 for d in returns.values()),'note':'Final physical proximity audit; full PCB connectivity and DRC are checked separately.'},indent=2)+'\n')
    critical={'/USB_N','/USB_P','/USB_DM','/USB_DP','/XIN','/XOUT','/XTAL_OUT'}
    critical_lines=[]
    def line(t):return LineString([(pcbnew.ToMM(p.x),pcbnew.ToMM(p.y)) for p in [t.GetStart(),t.GetEnd()]])
    for t in board.GetTracks():
        if t.GetNetname() in critical:
            require(t.GetClass()=='PCB_TRACK' and t.GetLayer()==pcbnew.B_Cu,'USB/clock signals entirely bottom, zero signal vias')
            if t.GetClass()=='PCB_TRACK':critical_lines.append(line(t))
    for t in board.GetTracks():
        if t.GetClass()=='PCB_TRACK' and t.GetLayer()==pcbnew.In2_Cu and t.GetNetname()!='/GND':require(all(line(t).distance(g)>=.65+pcbnew.ToMM(t.GetWidth())/2-.001 for g in critical_lines),'Adjacent In2 USB/clock ground-reference corridor')
    for p in [1,10,22,33,42,43,44,48,49]:require(net('U1',p)=='3V3',f'U1 supply {p}')
    for p in [23,45,50]:require(net('U1',p)=='1V1',f'U1 core supply {p}')
    for p in [19,57]:require(net('U1',p)=='GND',f'U1 ground/test {p}')
    require(net('U1',46)=='USB_DM' and net('U1',47)=='USB_DP','USB RP2040 pin order')
    for n,g in {**{i+2:i for i in range(8)},**{i+3:i for i in range(8,16)},**{i+11:i for i in range(16,22)},34:22,38:26}.items():
        require(net('U1',n)==(f'ROW{g}' if g<8 else f'COL{g-8:02d}' if g<23 else 'COL15'),f'GPIO mapping GP{g}')
    require(net('U1',39)=='RGB_DATA' and net('U1',40)=='LED_EN','LED GPIO mapping')
    for pin,n in {1:'QSPI_SS',2:'QSPI_SD1',3:'QSPI_SD2',4:'GND',5:'QSPI_SD0',6:'QSPI_SCLK',7:'QSPI_SD3',8:'3V3'}.items():require(net('U4',pin)==n,f'Flash pin {pin}')
    require('SOIC-8W_5.3x5.3' in str(fps['U4'].GetFPID().GetLibItemName()),'W25Q32JVSSIQ requires 208-mil SS package')
    for pin,n in {1:'RAW_USB_5V',2:'GND',3:'RAW_USB_5V',5:'3V3'}.items():require(net('U5',pin)==n,f'AP2112 pin {pin}')
    for p in ['A4','A9','B4','B9']:require(net('J1',p)=='RAW_USB_5V','Connector VBUS')
    for p in ['A1','A12','B1','B12','S1']:require(net('J1',p)=='GND','Connector ground')
    for ref,pin,name in [('R12',1,'CC1'),('R13',1,'CC2'),('J1','A5','CC1'),('J1','B5','CC2')]:require(net(ref,pin)==name,'Independent CC resistors')
    for ref in ['R12','R13']:require(fps[ref].GetValue()=='5.1k 1%' and net(ref,2)=='GND','CC pulldown value/ground')
    require(net('R15',1)=='QSPI_SS' and net('R15',2)=='BOOT_SW' and fps['R15'].GetValue()=='1k 1%','BOOTSEL isolation')
    require(net('BTN1',1)=='BOOT_SW' and net('BTN1',2)=='GND','BOOTSEL button')
    require(net('BTN2',1)=='RUN' and net('BTN2',2)=='GND' and net('R17',2)=='3V3','RUN reset and pullup')
    require(net('F1',1)=='RAW_USB_5V' and net('F1',2)=='FUSED_5V','Fused LED branch')
    require(net('U3',1)=='FUSED_5V' and net('U3',6)=='LED_5V' and net('U3',3)=='LED_EN','TPS2553 branch')
    require(fps['R4'].GetValue()=='75k 1%' and fps['R2'].GetValue()=='100k','Current limit / default-off')
    require('TP1' not in fps and not any('YD_RP2040' in str(f.GetFPID().GetLibItemName()) for f in fps.values()),'No module or VBUS wire pad')
    baseline=json.loads((ROOT/'source/legacy-data.json').read_text())
    original=pcbnew.LoadBoard(str(ROOT/'source/legacy-base.kicad_pcb'))
    original_fps={f.GetReference():f for f in original.GetFootprints()}
    def shape(s):
        return (int(s.GetShape()),s.GetStart().x,s.GetStart().y,s.GetEnd().x,s.GetEnd().y,s.GetWidth())
    def pad_geometry(f):
        return sorted((p.GetNumber(),p.GetPosition().x,p.GetPosition().y,p.GetSize().x,p.GetSize().y,p.GetDrillSize().x,p.GetDrillSize().y,p.GetOrientationDegrees(),int(p.GetShape()),tuple(p.GetLayerSet().Seq())) for p in f.Pads())
    require(sorted(shape(s) for s in board.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts)==sorted(shape(s) for s in original.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts),'Preserved board outline')
    for ref in [k['ref'] for k in baseline['keys']]+[k['led_ref'] for k in baseline['keys']]+[f'H{i}' for i in range(1,12)]:
        old,new=original_fps[ref],fps[ref]
        require(old.GetOrientationDegrees()==new.GetOrientationDegrees() and old.GetLayer()==new.GetLayer(),f'Preserved orientation/side {ref}')
        require(sorted(shape(s) for s in old.GraphicalItems() if s.GetLayer()==pcbnew.Edge_Cuts)==sorted(shape(s) for s in new.GraphicalItems() if s.GetLayer()==pcbnew.Edge_Cuts),f'Preserved footprint cutouts {ref}')
    require(len([f for r,f in fps.items() if r.startswith('SW')])==117,'117 MX switches')
    require(len([f for r,f in fps.items() if r.startswith('LED')])==117,'117 LEDs')
    addresses=set()
    for k in baseline['keys']:
        addresses.add((k['matrix_row'],k['matrix_col']))
        for ref in [k['ref'],k['diode'],k['led_ref'],k['cap_ref']]:
            old=next(p for p in baseline['parts'] if p['ref']==ref);pos=fps[ref].GetPosition()
            require(abs(pcbnew.ToMM(pos.x)-old['x'])<.00001 and abs(pcbnew.ToMM(pos.y)-old['y'])<.00001,f'Preserved position {ref}')
            require(pad_geometry(fps[ref])==pad_geometry(original_fps[ref]),f'Preserved pad/hole geometry {ref}')
        require(net(k['ref'],1)==f"ROW{k['matrix_row']}" and net(k['ref'],2)==k['key_net'],'Matrix switch')
        require(net(k['diode'],1)==f"COL{k['matrix_col']:02d}" and net(k['diode'],2)==k['key_net'],'ROW2COL diode')
        require(net(k['led_ref'],2)==k['rgb_in'],'LED order')
        if k['rgb_out']:require(net(k['led_ref'],4)==k['rgb_out'],'LED chain continuation')
    require(len(addresses)==117,'Unique matrix addresses')
    for i,(x,y) in enumerate(baseline['mounts'],1):
        pos=fps[f'H{i}'].GetPosition();require(abs(pcbnew.ToMM(pos.x)-x)<.00001 and abs(pcbnew.ToMM(pos.y)-y)<.00001,f'Mount H{i}')
    fw=json.loads((ROOT/'firmware/keyboard.json').read_text())
    require(fw['rgb_matrix']['max_brightness']==8 and len(fw['rgb_matrix']['layout'])==117,'Conservative RGB firmware')
    require(fw['matrix_pins']['rows']==[f'GP{i}' for i in range(8)] and fw['matrix_pins']['cols']==[f'GP{i}' for i in range(8,23)]+['GP26'],'Firmware matrix')
    require('(4 * 1024 * 1024)' in (ROOT/'firmware/config.h').read_text(),'4MB firmware flash capacity')
    erc=json.loads((report/'erc.json').read_text());drc=json.loads((report/'drc.json').read_text())
    ev=sum(len(s.get('violations',[])) for s in erc['sheets'])
    result=dict(kicad=pcbnew.Version(),erc=ev,drc=len(drc['violations']),unconnected=len(drc['unconnected_items']),schematic_parity=len(drc['schematic_parity']),assertion_issues=issues,hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [pcb,sch,ROOT/(NAME+'.kicad_pro')]})
    result['fabrication_ready']=False
    result['assembly']={'side':'B','top_smd_pads':top_smd,'top_paste_pads':top_paste,'bottom_smd_pads':bottom_smd,'checked_controller_courtyards':len(courtyards),'checked_controller_bodies':len(bodies),'off_ep_ground_vias':len(epvias),'ep_bottom_paste_windows':len(paste)}
    settings=json.loads((ROOT/(NAME+'.kicad_pro')).read_text())['board']['design_settings']
    result['ignored_drc_categories']=[k for k,v in settings['rule_severities'].items() if v=='ignore']
    require(set(result['ignored_drc_categories'])=={'footprint_filters_mismatch','footprint_type_mismatch','missing_courtyard','track_not_centered_on_via','tuning_profile_track_geometries'},'No new ignored DRC categories')
    require(not settings['drc_exclusions'],'No DRC exclusions')
    result['electrical_checks_pass']=not any([result[k] for k in ['erc','drc','unconnected','schematic_parity']]+[issues])
    result['release_blockers']=['Inherited LED aperture corner/tolerance fit not qualified','Factory DFM and stackup/USB signal integrity review','Physical case/plate fit and assembled-board USB/power/functional tests']
    (report/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['electrical_checks_pass'] else 1
if __name__=='__main__':sys.exit(main())
