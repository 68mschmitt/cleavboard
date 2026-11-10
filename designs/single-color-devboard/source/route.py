"""Temporary conservative-grid completion, always followed by real KiCad DRC."""
import argparse
import json
import math
import subprocess
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw

WORK = Path('/tmp/opencode/mono')
STEP = .05
X0=330
LAYERS = [pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu,pcbnew.In1_Cu]
W,H = math.ceil((452.4375-X0)/STEP)+1,math.ceil(80/STEP)+1


def xy(point):
    return pcbnew.ToMM(point.x)-X0,pcbnew.ToMM(point.y)


def point(x,y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x+X0),pcbnew.FromMM(y))


def circle(draw,x,y,r):
    draw.ellipse(((x-r)/STEP,(y-r)/STEP,(x+r)/STEP,(y+r)/STEP),fill=1)


def rect(draw,bbox,r,rounded=True):
    a,b,c,d = bbox
    bounds = ((a-r)/STEP,(b-r)/STEP,(c+r)/STEP,(d+r)/STEP)
    if rounded:
        draw.rounded_rectangle(bounds,radius=r/STEP,fill=1)
    else:
        draw.rectangle(bounds,fill=1)


def capsule(draw,a,b,r):
    draw.line([(a[0]/STEP,a[1]/STEP),(b[0]/STEP,b[1]/STEP)],fill=1,width=math.ceil(2*r/STEP)+1)
    circle(draw,*a,r);circle(draw,*b,r)


def bounds(item):
    box=item.GetBoundingBox()
    return (pcbnew.ToMM(box.GetX())-X0,pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight())-X0,pcbnew.ToMM(box.GetBottom()))


def masks(board,net,width):
    images=[Image.new('L',(W,H),0) for _ in LAYERS]
    via_image=Image.new('L',(W,H),0)
    draws=[ImageDraw.Draw(i) for i in images]; vd=ImageDraw.Draw(via_image)
    tr=width/2+.23; vr=.3+.23
    for fp in board.GetFootprints():
        if fp.GetReference().startswith('H'):
            x,y=xy(fp.GetPosition())
            for draw in draws:circle(draw,x,y,3+width/2+.03)
            circle(vd,x,y,3.28)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            x,y=xy(pad.GetPosition())
            copper=[i for i,layer in enumerate(LAYERS) if pad.IsOnLayer(layer)]
            drill=pcbnew.ToMM(pad.GetDrillSize().x)/2
            if pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                for draw in draws:circle(draw,x,y,drill+.25+width/2+.03)
                circle(vd,x,y,drill+.25+.3+.03)
                continue
            is_circle=pad.GetShape()==pcbnew.PAD_SHAPE_CIRCLE
            if pad.GetNetCode()!=net.GetNetCode():
                for i in copper:
                    if is_circle:circle(draws[i],x,y,pcbnew.ToMM(pad.GetSize().x)/2+tr)
                    else:rect(draws[i],bounds(pad),tr)
                if is_circle:circle(vd,x,y,pcbnew.ToMM(pad.GetSize().x)/2+vr)
                else:rect(vd,bounds(pad),vr)
            else:
                if drill:
                    circle(vd,x,y,drill+.25+.3+.03)
                else:
                    rect(vd,bounds(pad),.4)
        for shape in fp.GraphicalItems():
            if shape.GetLayer()==pcbnew.Edge_Cuts:
                for draw in draws:rect(draw,bounds(shape),.5+width/2+.03)
                rect(vd,bounds(shape),.5+.3+.03)
    for item in board.GetTracks():
        if item.GetClass()=='PCB_VIA':
            x,y=xy(item.GetPosition())
            if item.GetNetCode()==net.GetNetCode():
                circle(vd,x,y,pcbnew.ToMM(item.GetDrillValue())/2+.25+.3+.03)
            else:
                r=pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu))/2
                for draw in draws:circle(draw,x,y,r+tr)
                circle(vd,x,y,r+vr)
        elif item.GetNetCode()!=net.GetNetCode():
            r=pcbnew.ToMM(item.GetWidth())/2
            if item.GetLayer() in LAYERS:
                capsule(draws[LAYERS.index(item.GetLayer())],xy(item.GetStart()),xy(item.GetEnd()),r+tr)
            # A through-via also has to clear copper on the reserved inner layer.
            capsule(vd,xy(item.GetStart()),xy(item.GetEnd()),r+vr)
    for draw,margin in [(d,.5+width/2+.05) for d in draws]+[(vd,.85)]:
        m=math.ceil(margin/STEP)
        draw.rectangle((0,0,W-1,m),fill=1);draw.rectangle((0,H-1-m,W-1,H-1),fill=1)
        draw.rectangle((0,0,m,H-1),fill=1);draw.rectangle((W-1-m,0,W-1,H-1),fill=1)
    # Keep In1 exclusively as a ground return plane.
    draws[3].rectangle((0,0,W,H),fill=1)
    # Reserve adjacent In2 ground corridors under bottom USB and clock copper.
    # Other In2 space permits short GPIO escape crossings out of the via ring.
    for item in board.GetTracks():
        if item.GetClass()=='PCB_TRACK' and item.GetLayer()==pcbnew.B_Cu and item.GetNetname() in ['/USB_N','/USB_P','/USB_DM','/USB_DP','/XIN','/XOUT','/XTAL_OUT']:
            capsule(draws[1],xy(item.GetStart()),xy(item.GetEnd()),.65+width/2)
    return images,via_image


def terminals(item,board):
    if item.GetClass()=='PCB_TRACK':
        a,b=xy(item.GetStart()),xy(item.GetEnd())
        length=math.dist(a,b)
        steps=max(1,math.ceil(length/2))
        points=[(a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps) for i in range(steps+1)]
        layers=[LAYERS.index(item.GetLayer())]
    else:
        points=[xy(item.GetPosition())]
        layers=range(len(LAYERS)) if item.GetClass()=='PCB_VIA' else [i for i,l in enumerate(LAYERS) if item.IsOnLayer(l)]
    result={(z,round(x/STEP),round(y/STEP)):(x,y) for z in layers for x,y in points}
    if item.GetClass()=='PCB_TRACK':
        for via in board.GetTracks():
            if via.GetClass()!='PCB_VIA' or via.GetNetCode()!=item.GetNetCode():continue
            position=xy(via.GetPosition())
            if min(math.dist(position,a),math.dist(position,b))<.001:
                for z in range(len(LAYERS)):
                    result[(z,round(position[0]/STEP),round(position[1]/STEP))]=position
    return result


def apply(board,net,width,path,starts,goals):
    def track(layer,a,b):
        if math.dist(a,b)<.00001:return
        t=pcbnew.PCB_TRACK(board);t.SetLayer(LAYERS[layer]);t.SetStart(point(*a));t.SetEnd(point(*b))
        t.SetNet(net);t.SetWidth(pcbnew.FromMM(width));board.Add(t)
    # Compress consecutive grid steps into real straight copper segments.
    vertices=[path[0]]
    direction=None
    for a,b in zip(path,path[1:]):
        delta=tuple(bb-aa for aa,bb in zip(a,b))
        if direction is not None and delta!=direction and vertices[-1]!=a:vertices.append(a)
        direction=delta
    if vertices[-1]!=path[-1]:vertices.append(path[-1])
    start=path[0];end=path[-1]
    track(start[0],starts[start],(start[1]*STEP,start[2]*STEP))
    positions={(t.GetPosition().x,t.GetPosition().y) for t in board.GetTracks()
               if t.GetClass()=='PCB_VIA' and t.GetNetCode()==net.GetNetCode()}
    for a,b in zip(vertices,vertices[1:]):
        if a[0]!=b[0]:
            pos=point(a[1]*STEP,a[2]*STEP)
            if (pos.x,pos.y) not in positions:
                via=pcbnew.PCB_VIA(board);via.SetPosition(pos);via.SetWidth(pcbnew.FromMM(.6))
                via.SetDrill(pcbnew.FromMM(.3));via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
                via.SetNet(net);board.Add(via);positions.add((pos.x,pos.y))
        else:track(a[0],(a[1]*STEP,a[2]*STEP),(b[1]*STEP,b[2]*STEP))
    track(end[0],(end[1]*STEP,end[2]*STEP),goals[end])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board',type=Path);parser.add_argument('report',type=Path)
    parser.add_argument('--limit',type=int,default=10)
    parser.add_argument('--step',type=float,default=.05,help='Grid in mm')
    args=parser.parse_args()
    global STEP,W,H
    STEP=args.step;W,H=math.ceil((452.4375-X0)/STEP)+1,math.ceil(80/STEP)+1
    args.board=args.board.resolve()
    board=pcbnew.LoadBoard(str(args.board))
    report=json.loads(args.report.read_text())
    items={t.m_Uuid.AsString():t for t in board.GetTracks()}
    items.update({p.m_Uuid.AsString():p for fp in board.GetFootprints() for p in fp.Pads()})
    attempted=0
    def priority(v):
        text=str(v)
        return 0 if any(n in text for n in ['USB_','QSPI_','XIN','XOUT','XTAL_']) else 1 if any(n in text for n in ['3V3','1V1','GND']) else 2
    for violation in sorted(report['unconnected_items'],key=priority):
        if attempted>=args.limit:break
        a,b=[items.get(p['uuid']) for p in violation['items']]
        if a is None or b is None:continue
        net=a.GetNet();width=.4 if net.GetNetname() in ['/LED_5V','/MODULE_VOUT','/FUSED_5V'] else .3
        board.BuildConnectivity()
        conn=board.GetConnectivity()
        def cluster(item):
            result={}
            for obj in [item]+list(conn.GetConnectedItems(item)):
                if obj.GetClass() not in ['PAD','PCB_TRACK','PCB_VIA']:continue
                if obj.GetClass()=='PCB_TRACK' and obj.GetLayer() not in LAYERS:continue
                result.update(terminals(obj,board))
            return {p:v for p,v in result.items() if 0<=p[1]<W and 0<=p[2]<H}
        starts,goals=cluster(a),cluster(b)
        if len(starts)>len(goals):starts,goals=goals,starts
        if set(starts)&set(goals):continue
        if not starts or not goals:continue
        print('Route',net.GetNetname(),len(starts),len(goals),flush=True)
        images,viamask=masks(board,net,width)
        root=WORK/'grid-current'
        (root.with_suffix('.maps')).write_bytes(b''.join(i.tobytes() for i in images))
        (root.with_suffix('.vias')).write_bytes(viamask.tobytes())
        (root.with_suffix('.points')).write_text(f'{W} {H} {len(starts)} {len(goals)}\n'+
            ''.join(f'{z} {x} {y}\n' for z,x,y in list(starts)+list(goals)))
        result=subprocess.run([str(WORK/'grid-route'),str(root)],capture_output=True,text=True)
        print(result.stdout.strip(),flush=True)
        if result.returncode:continue
        rows=(root.with_suffix('.path')).read_text().splitlines()[1:]
        path=[tuple(map(int,row.split())) for row in rows]
        apply(board,net,width,path,starts,goals);attempted+=1
        pcbnew.SaveBoard(str(args.board),board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.board),board)
    print('Added',attempted,'connections; mandatory fresh KiCad DRC is next.',flush=True)


if __name__=='__main__':main()
