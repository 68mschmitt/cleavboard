#!/usr/bin/env python3
"""Independent schematic/PCB, placement, power, aperture and assembly assertions."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys,math
import xml.etree.ElementTree as ET
import pcbnew
from shapely.geometry import box,Point,LineString
ROOT=Path(__file__).resolve().parents[1]
NAME='Cleaver-White'
def main():
    report=ROOT/'validation';pcb=ROOT/(NAME+'.kicad_pcb');sch=ROOT/(NAME+'.kicad_sch')
    def run(args):subprocess.run(['kicad-cli']+list(map(str,args)),check=True)
    # Persist filled copper; DRC also independently requests refill.
    b=pcbnew.LoadBoard(str(pcb));pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(pcb),b)
    run(['sch','export','netlist','--format','kicadxml','-o',report/'netlist.xml',sch])
    run(['sch','erc','--format','json','--severity-all','-o',report/'erc.json',sch])
    run(['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',report/'drc.json',pcb])
    fps={f.GetReference():f for f in b.GetFootprints()};base=pcbnew.LoadBoard(str(ROOT/'source/base-rev04.kicad_pcb'));old={f.GetReference():f for f in base.GetFootprints()}
    data=json.loads((ROOT/'source/layout.json').read_text());components=json.loads((ROOT/'source/components.json').read_text())
    netlist=ET.parse(report/'netlist.xml').getroot();nets={(n.get('ref'),n.get('pin')):net.get('name') for net in netlist.findall('./nets/net') for n in net.findall('node')}
    issues=[];count=0
    def require(ok,msg):
        nonlocal count
        count+=1
        if not ok:issues.append(msg)
    def pad(ref,num):return next(p for p in fps[ref].Pads() if p.GetNumber()==str(num))
    def net(ref,num):return pad(ref,num).GetNetname().lstrip('/')
    def pos(o):return (o.GetPosition().x,o.GetPosition().y)
    def geom(f):return sorted((p.GetNumber(),pos(p),p.GetSize().x,p.GetSize().y,p.GetDrillSize().x,p.GetDrillSize().y,p.GetOrientationDegrees(),int(p.GetShape()),tuple(p.GetLayerSet().Seq())) for p in f.Pads())
    def shape(s):return (int(s.GetShape()),s.GetStart().x,s.GetStart().y,s.GetEnd().x,s.GetEnd().y)
    require(sorted(shape(s) for s in b.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts)==sorted(shape(s) for s in base.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts),'Original outer outline')
    top_paste=[];top_smd=[];tht=[]
    for f in fps.values():
        for p in f.Pads():
            key=(f.GetReference(),p.GetNumber())
            if key in nets:require(p.GetNetname()==nets[key],f'Schematic parity {key}')
            if p.IsOnLayer(pcbnew.F_Paste):top_paste.append(key)
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu):top_smd.append(key)
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH:tht.append(key)
    require(not top_paste,'No F.Paste pads');require(not top_smd,'All SMD copper on underside')
    require(len(tht)==40 and all(r=='U1' for r,n in tht),'Only owner-soldered THT electronics: 40 module header pins')
    for ref in ['U1']+[f'H{i}' for i in range(1,12)]:require(geom(fps[ref])==geom(old[ref]),f'Original module/mount geometry {ref}')
    require(fps['U1'].GetLayer()==pcbnew.F_Cu,'TOP module')
    cells=set()
    for i,k in enumerate(data['keys'],1):
        sw,d,led=k['ref'],k['diode'],k['led_ref'];r=f'RL{i:03d}'
        require(geom(fps[sw])==geom(old[sw]),f'Original switch/socket holes and pads {sw}')
        require(geom(fps[d])==geom(old[d]),f'Original diode geometry {d}')
        require(net(sw,1)==f"ROW{k['matrix_row']}" and net(sw,2)==k['key_net'],f'Switch mapping {sw}')
        require(net(d,1)==f"COL{k['matrix_col']:02d}" and net(d,2)==k['key_net'],f'ROW2COL diode {d}')
        require(net(led,1)=='LED_RETURN' and net(led,2)==f'ANODE{i:03d}' and net(r,1)==f'ANODE{i:03d}' and net(r,2)=='LED_5V',f'One resistor per LED {led}')
        require(fps[r].GetValue()=='3.9k 1%' and fps[led].GetValue()=='BL-HZ333H-L21-TRE',f'Selected current and LED {led}')
        for ref,mpn,code,footprint in [(sw,'CPG151101S11-16','C41430893','HanElectricity_CPG151101S11-16'),(led,'BL-HZ333H-L21-TRE','C5123487','BL-HZ333H-L21-TRE_Reverse')]:
            require(fps[ref].GetValue()==mpn and fps[ref].GetFieldText('MPN')==mpn and fps[ref].GetFieldText('LCSC Part #')==code,f'Exact purchasing identity {ref}')
            require(str(fps[ref].GetFPID().GetLibItemName())==footprint,f'Exact footprint identity {ref}')
            comp=netlist.find(f'./components/comp[@ref="{ref}"]')
            require(comp is not None and comp.findtext('value')==mpn and comp.findtext('fields/field[@name="LCSC Part #"]')==code,f'Schematic catalog identity {ref}')
        require(fps[led].GetLayer()==pcbnew.B_Cu and fps[r].GetLayer()==pcbnew.B_Cu,f'Underside LED/resistor {led}')
        edges=[s for s in fps[led].GraphicalItems() if s.GetLayer()==pcbnew.Edge_Cuts]
        require(len(edges)==1,f'One optical aperture {led}')
        s=edges[0];require(abs(abs(s.GetEnd().x-s.GetStart().x)-pcbnew.FromMM(2.1))<2 and abs(abs(s.GetEnd().y-s.GetStart().y)-pcbnew.FromMM(2.3))<2,f'2.1x2.3 optical aperture {led}')
        cx,cy=pos(fps[led])
        for n,dx in [('1',-1.875),('2',1.875)]:
            p=pad(led,n);require(abs(p.GetPosition().x-cx-pcbnew.FromMM(dx))<2 and abs(p.GetPosition().y-cy)<2 and p.GetSize()==pcbnew.VECTOR2I(pcbnew.FromMM(1.35),pcbnew.FromMM(1.6)),f'K/A reverse-mount land geometry {led}.{n}')
        cells.add((k['matrix_row'],k['matrix_col']))
    require(len(cells)==117,'117 unique matrix circuits')
    for prefix in ['SW','LED','RL']:require(sum(r.startswith(prefix) for r in fps)==117,f'117 {prefix}')
    for r in range(8):
        n=next(n for n,g in data['module_pins'].items() if g==f'GP{r}');require(net('U1',n)==f'ROW{r}',f'Row GPIO {r}')
    for c,g in enumerate(list(range(8,23))+[26]):
        n=next(n for n,v in data['module_pins'].items() if v==f'GP{g}');require(net('U1',n)==f'COL{c:02d}',f'Column GPIO {g}')
    require(net('U1',40)=='MODULE_VOUT' and net('U1',32)=='BL_PWM' and net('U1',34)=='LED_EN','Header power and brightness control')
    for n in [35,36,37,39]:require(pad('U1',n).GetNetname().startswith('unconnected-'),f'Unused module rail/GPIO {n}')
    for ref,n,want in [('F1',1,'MODULE_VOUT'),('F1',2,'FUSED_5V'),('U3',1,'FUSED_5V'),('U3',5,'FUSED_5V'),('U3',6,'LED_5V'),('U3',2,'GND'),('U3',3,'LED_EN'),('R2',1,'LED_EN'),('R2',2,'GND'),('R1',1,'BL_PWM'),('R1',2,'GATE'),('R3',1,'GATE'),('R3',2,'GND'),('Q1',1,'GATE'),('Q1',2,'GND'),('Q1',3,'LED_RETURN'),('C1',1,'FUSED_5V'),('C1',2,'GND'),('C2',1,'LED_5V'),('C2',2,'GND')]:require(net(ref,n)==want,f'Power path {ref}.{n}')
    require(fps['F1'].GetValue()=='1206L020YR 0.20A hold','Exact PTC')
    require(fps['R2'].GetValue()==fps['R3'].GetValue()=='100k 1%','Reset-off pull-downs')
    require(fps['Q1'].GetValue()=='AO3400A' and fps['R1'].GetValue()=='330R 1%','Qualified logic MOSFET/gate resistor')
    require('C5' not in fps and 'TP1' not in fps and 'U2' not in fps,'No TH bulk, power wire or RGB translator')
    # Same-side physical bodies, including actual underside socket bodies.
    bodies={}
    for p in components:
        ref=p['ref'];f=fps[ref]
        if p['kind'] in ['YD_RP2040','TestPad']:continue
        shapes=[s for s in f.GraphicalItems() if s.GetClass()=='PCB_SHAPE' and s.GetLayer()==pcbnew.B_Fab]
        require(bool(shapes),f'Bottom assembly body {ref}')
        if not shapes:continue
        boxes=[s.GetBoundingBox() for s in shapes]
        bodies[ref]=box(min(v.GetX() for v in boxes)/1e6,min(v.GetY() for v in boxes)/1e6,max(v.GetRight() for v in boxes)/1e6,max(v.GetBottom() for v in boxes)/1e6)
    refs=list(bodies)
    for i,r in enumerate(refs):
        for s in refs[i+1:]:require(bodies[r].intersection(bodies[s]).area<1e-7,f'Bottom body collision {r}/{s}')
        for x,y in data['mounts']:require(not bodies[r].intersects(Point(x,y).buffer(3)),f'6mm mounting envelope {r}')
    # All vias stay outside paste/solder lands; no costly via-in-pad process.
    smd=[(f.GetReference(),p,box(p.GetBoundingBox().GetX()/1e6,p.GetBoundingBox().GetY()/1e6,p.GetBoundingBox().GetRight()/1e6,p.GetBoundingBox().GetBottom()/1e6)) for f in fps.values() for p in f.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    for v in b.GetTracks():
        if v.GetClass()!='PCB_VIA':continue
        pt=Point(v.GetPosition().x/1e6,v.GetPosition().y/1e6)
        for ref,p,g in smd:
            if abs(p.GetPosition().x-v.GetPosition().x)>pcbnew.FromMM(3) or abs(p.GetPosition().y-v.GetPosition().y)>pcbnew.FromMM(3):continue
            require(pt.distance(g)>=pcbnew.ToMM(v.GetDrillValue())/2+.099,f'Off-pad via {ref}.{p.GetNumber()}')
    fw=json.loads((ROOT/'firmware/keyboard.json').read_text())
    require(fw['matrix_pins']['rows']==[f'GP{i}' for i in range(8)] and fw['matrix_pins']['cols']==[f'GP{i}' for i in list(range(8,23))+[26]],'Firmware matrix')
    require('rgb_matrix' not in fw and 'ws2812' not in fw and fw['features']['backlight'],'Monochrome firmware')
    require(fw['usb']['max_power']==200,'Conservative USB descriptor')
    require('(4 * 1024 * 1024)' in (ROOT/'firmware/config.h').read_text(),'4MB flash')
    settings=json.loads((ROOT/(NAME+'.kicad_pro')).read_text())['board']['design_settings']
    ignored=[k for k,v in settings['rule_severities'].items() if v=='ignore']
    require(set(ignored)=={'footprint_filters_mismatch','footprint_type_mismatch','missing_courtyard','track_not_centered_on_via','tuning_profile_track_geometries'},'No added ignored categories')
    require(not settings['drc_exclusions'],'No DRC exclusions')
    from check_replacements import verify
    replacement_report=verify(b,require)
    (report/'replacements.json').write_text(json.dumps(replacement_report,indent=2)+'\n')
    erc=json.loads((report/'erc.json').read_text());drc=json.loads((report/'drc.json').read_text())
    result=dict(kicad=pcbnew.Version(),erc=sum(len(s.get('violations',[])) for s in erc['sheets']),drc=len(drc['violations']),unconnected=len(drc['unconnected_items']),schematic_parity=len(drc['schematic_parity']),assertion_count=count,assertion_issues=issues,ignored_baseline_categories=ignored,custom_rules=['Only LED solder lands: edge clearance 0.1mm, nominal 0.15mm'],assembly=dict(top_paste=top_paste,top_smd=top_smd,through_hole_electronic_pads=len(tht),checked_bottom_bodies=len(bodies)),fabrication_ready=False)
    result['electrical_checks_pass']=not any([result[k] for k in ['erc','drc','unconnected','schematic_parity']]+[issues])
    result['hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [pcb,sch,ROOT/(NAME+'.kicad_pro'),ROOT/(NAME+'.kicad_dru')]}
    (report/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['electrical_checks_pass'] else 1
if __name__=='__main__':sys.exit(main())
