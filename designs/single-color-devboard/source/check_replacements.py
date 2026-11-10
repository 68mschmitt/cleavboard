"""Independent datasheet envelope checks against actual, placed KiCad geometry.

Dimensions are transcribed from the two saved vendor drawings, not imported from
the generator. This cannot establish terminal wetting or physical brightness.
"""
from itertools import product
from shapely.geometry import box
from shapely.affinity import rotate, translate
import pcbnew


def verify(board, require):
    fps={f.GetReference():f for f in board.GetFootprints()}
    mm=lambda p:(p.x/1e6,p.y/1e6)
    # Minimum finished opening, maximum allowed router radius; registration and
    # placement offsets combine in the worst direction. Rotation is sampled
    # over the whole assumed +/-3 degree placement envelope.
    opening=box(-1.025+.25,-1.125+.25,1.025-.25,1.125-.25).buffer(.25,quad_segs=128)
    lens=box(-1.45/2,-1.70/2,1.45/2,1.70/2)
    margins=[]
    for dx,dy,angle in product([-.125,.125],[-.125,.125],[i/10 for i in range(-30,31)]):
        moved=translate(rotate(lens,angle,origin=(0,0)),dx,dy)
        require(opening.contains(moved),f'BrtLed maximum lens in minimum rounded opening {dx}/{dy}/{angle}')
        margins.append(opening.boundary.distance(moved))
    # Conservative full-package-height bound (even ignoring carrier thickness).
    require(1.10+.10 < 1.6*.9,'LED maximum total height below minimum 10%-tolerance PCB thickness')
    min_overlap=99
    for i in range(1,118):
        f=fps[f'LED{i:03d}'];cx,cy=mm(f.GetPosition())
        pads={p.GetNumber():p for p in f.Pads()}
        require(pads['1'].GetPosition().x < pads['2'].GetPosition().x,f'LED{i:03d} cathode left in top view')
        require(all(p.IsOnLayer(pcbnew.B_Paste) for p in pads.values()),f'LED{i:03d} bottom reflow')
        # Nominally unrotated minimum-length substrate support over both lands;
        # electrode notches are not sufficiently dimensioned to assert wetting.
        for n in ['1','2']:
            p=pads[n];px,py=mm(p.GetPosition());sx,sy=mm(p.GetSize())
            inner=abs(px-cx)-sx/2
            overlap=3.1/2-.1-inner
            min_overlap=min(min_overlap,overlap)
            require(overlap >= .25-1e-8,f'LED{i:03d}.{n} minimum substrate overlap')
            require(inner-1.075-.025 >= .10-1e-8,f'LED{i:03d}.{n} worst copper-to-aperture gap')
        f=fps[f'SW{i:03d}'];cx,cy=mm(f.GetPosition())
        pads={p.GetNumber():p for p in f.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD}
        for n,dx,dy in [('1',6.29,-5.08),('2',-7.56,-2.54)]:
            p=pads[n];px,py=mm(p.GetPosition())
            require(abs(px-cx-dx)<1e-6 and abs(py-cy-dy)<1e-6,f'SW{i:03d}.{n} HanElectricity terminal position')
            require(mm(p.GetSize())==(2.55,2.5) and p.IsOnLayer(pcbnew.B_Paste),f'SW{i:03d}.{n} vendor-size bottom land')
        holes=[p for p in f.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH and abs(p.GetDrillSize().x/1e6-3)<1e-6]
        locations=sorted((round(p.GetPosition().x/1e6-cx,6),round(p.GetPosition().y/1e6-cy,6)) for p in holes)
        require(locations==[(-3.81,-2.54),(2.54,-5.08)],f'SW{i:03d} 3mm socket holes, 6.35x2.54 spacing')
    # Maximum purchased body envelopes including +/-0.1mm XY placement.
    # Socket includes full terminal span, not only the plastic body.
    envelopes={}
    for ref,f in fps.items():
        x,y=mm(f.GetPosition())
        if ref.startswith('SW'):
            x-=.635;y-=3.81;envelopes[ref]=box(x-7.55,y-3.07,x+7.55,y+3.07)
        elif ref.startswith('LED'):
            envelopes[ref]=translate(rotate(box(-1.65,-.85,1.65,.85),3,origin=(0,0)).envelope.buffer(.1,join_style='mitre'),x,y)
        else:
            shapes=[s.GetBoundingBox() for s in f.GraphicalItems() if s.GetClass()=='PCB_SHAPE' and s.GetLayer()==pcbnew.B_Fab]
            if shapes and any(p.IsOnLayer(pcbnew.B_Paste) for p in f.Pads()):
                envelopes[ref]=box(min(s.GetX() for s in shapes)/1e6,min(s.GetY() for s in shapes)/1e6,max(s.GetRight() for s in shapes)/1e6,max(s.GetBottom() for s in shapes)/1e6)
    gaps=[]
    for ref,body in envelopes.items():
        if not ref.startswith(('SW','LED')):continue
        for other,shape in envelopes.items():
            if ref==other:continue
            gap=body.distance(shape);gaps.append(gap)
            require(gap>0,f'Replacement envelope collision {ref}/{other}')
    # Individual resistors limit even a shorted LED far below its 20mA rating;
    # TPS2553 separately limits aggregate branch current to <=100mA steady state.
    short_led_current=5.25/(3900*.99)
    require(short_led_current < .020,'Resistor-only branch upper bound below LED 20mA maximum')
    return dict(socket='HanElectricity CPG151101S11-16 / C41430893',led='BrtLed BL-HZ333H-L21-TRE / C5123487',
                socket_count=117,led_count=117,minimum_lens_edge_margin_mm=min(margins),
                minimum_unrotated_substrate_overlap_mm=min_overlap,minimum_body_gap_mm=min(gaps),
                worst_resistor_only_branch_current_mA=short_led_current*1000,
                assumptions=dict(aperture_size_tolerance_mm=.05,aperture_registration_mm=.025,
                                 max_internal_corner_radius_mm=.25,placement_xy_mm=.1,led_rotation_degrees=3),
                physical_reflow_and_brightness_tested=False,jlcpcb_rotation_mapping_confirmed=False)
