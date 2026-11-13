"""Assembly regressions: physical side, socket origins, holes and probe pads."""
import math
import json
import unittest
import pcbnew
from design import ROOT, BOARD_H, MOUNTING_HOLES, TEST_POINTS, read_keys
from export_manufacturing import assembly_rows


class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board=pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
        cls.footprints={fp.GetReference():fp for fp in cls.board.GetFootprints()}

    def test_all_populated_smd_bottom_with_socket_centroids(self):
        groups,rows,pads=assembly_rows(self.board)
        self.assertEqual(len(rows),489)
        self.assertEqual(len(groups),14)
        self.assertEqual(sum(len(refs) for refs in groups.values()),489)
        byref={row[0]:row for row in rows}
        self.assertTrue(all(row[3]=='bottom' for row in rows))
        self.assertFalse(set(byref)&{'U1','TP1','TP2','TP3','TP4','TP5','TP6'})
        for key in read_keys()[0]:
            row=byref[key['ref']]
            self.assertAlmostEqual(float(row[1]),key['x']-.635,places=5)
            self.assertAlmostEqual(float(row[2]),BOARD_H-key['y']+3.81,places=5)
        self.assertEqual(self.footprints['U1'].GetLayer(),pcbnew.F_Cu)
        self.assertEqual(self.footprints['C5'].GetLayer(),pcbnew.B_Cu)

    def test_jlc_catalog_rotations_only_correct_u2_and_switch_sockets(self):
        angles={ref:fp.GetOrientationDegrees() for ref,fp in self.footprints.items()}
        _,rows,_=assembly_rows(self.board)
        byref={row[0]:row for row in rows}
        self.assertEqual(float(byref['U2'][4]),90)
        for key in read_keys()[0]:
            self.assertEqual(float(byref[key['ref']][4]),180)
        for ref,row in byref.items():
            if ref=='U2' or ref.startswith('SW'):continue
            self.assertEqual(float(row[4]),angles[ref]%360,ref)
        self.assertEqual(angles,{ref:fp.GetOrientationDegrees() for ref,fp in self.footprints.items()})

    def test_no_plated_through_hole_component_connections(self):
        holes=[]
        for ref,fp in self.footprints.items():
            for pad in fp.Pads():
                if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH:
                    holes.append((ref,pad.GetNumber()))
                self.assertFalse(pad.IsOnLayer(pcbnew.F_Paste),ref)
                if pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:
                    self.assertTrue(pad.IsOnLayer(pcbnew.B_Cu),ref)
        self.assertEqual(holes,[])

    def test_socket_replacement_preserves_vendor_holes_and_lands(self):
        for key in read_keys()[0]:
            fp=self.footprints[key['ref']]
            self.assertEqual(fp.GetLayer(),pcbnew.B_Cu)
            self.assertEqual(fp.GetField('LCSC').GetText(),'C41430893')
            self.assertEqual(fp.GetValue(),'CPG151101S11-16')
            pads={p.GetNumber():p for p in fp.Pads() if p.GetNumber()}
            for n,dx,dy in [('1',6.29,-5.08),('2',-7.56,-2.54)]:
                pad=pads[n];x,y=pcbnew.ToMM(pad.GetPosition())
                self.assertAlmostEqual(x,key['x']+dx,places=5)
                self.assertAlmostEqual(y,key['y']+dy,places=5)
                self.assertEqual(tuple(pcbnew.ToMM(pad.GetSize())),(2.55,2.5))
            holes=[p for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
            self.assertEqual(len(holes),5)
            for dx,dy in [(2.54,-5.08),(-3.81,-2.54)]:
                pad=next(p for p in holes if abs(pcbnew.ToMM(p.GetPosition().x)-key['x']-dx)<1e-5 and
                         abs(pcbnew.ToMM(p.GetPosition().y)-key['y']-dy)<1e-5)
                self.assertEqual(tuple(pcbnew.ToMM(pad.GetDrillSize())),(3.,3.))

    def test_every_purchasing_group_has_matching_live_smt_evidence(self):
        records={r['code']:r for filename in ('JLCPCB-2026-11-10.json','JLCPCB-2026-11-12.json')
                 for r in json.loads((ROOT/'references'/filename).read_text()) if 'component' in r}
        groups,_,_=assembly_rows(self.board)
        for manufacturer,mpn,code,package in groups:
            record=records[code];info=record['component'];stock=record['inventory']
            self.assertEqual(info['componentModelEn'],mpn)
            self.assertEqual(stock['componentCode'],code)
            self.assertEqual(info['assemblyMode'],'smtWeld')
            self.assertEqual(stock['isBuyComponent'],'1')
            self.assertIsNone(stock['noBuyReason'])
            self.assertGreater(stock['overseasStockCount'],0)
            self.assertGreater(stock['canPresaleNumber'],0)

    def test_capacitor_land_pattern_polarity_and_body_clearance(self):
        fp=self.footprints['C5'];pads={p.GetNumber():p for p in fp.Pads()}
        for n,x,net in [('1',373,'/LED_5V'),('2',381,'/GND')]:
            pad=pads[n]
            self.assertEqual(tuple(pcbnew.ToMM(pad.GetPosition())),(x,6.))
            self.assertEqual(tuple(pcbnew.ToMM(pad.GetSize())),(4.,2.))
            self.assertEqual(pad.GetNetname(),net)
        # Maximum 10.5 x 10.5 platform/can envelope; compare with real body
        # graphics of support parts and U1's bottom header pin lands.
        box=pcbnew.BOX2I(pcbnew.VECTOR2I(pcbnew.FromMM(371.75),pcbnew.FromMM(.75)),
                        pcbnew.VECTOR2I(pcbnew.FromMM(10.5),pcbnew.FromMM(10.5)))
        for ref,other in self.footprints.items():
            if ref in ['C5','LOGO1'] or ref.startswith(('H','FID','TP')):continue
            for graphic in other.GraphicalItems():
                if graphic.GetLayer()==pcbnew.B_Fab and graphic.GetClass()=='PCB_SHAPE':
                    self.assertFalse(box.Intersects(graphic.GetBoundingBox()),ref)
            if ref=='U1':
                for pad in other.Pads():self.assertFalse(box.Intersects(pad.GetBoundingBox()))

    def test_mounting_holes_and_reserved_copper(self):
        self.assertEqual(sum(z.GetIsRuleArea() for z in self.board.Zones()),len(MOUNTING_HOLES))
        for i,(x,y) in enumerate(MOUNTING_HOLES,1):
            fp=self.footprints[f'H{i}'];pad=list(fp.Pads())[0]
            self.assertEqual(tuple(pcbnew.ToMM(fp.GetPosition())),(x,y))
            self.assertEqual(pad.GetAttribute(),pcbnew.PAD_ATTRIB_NPTH)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetDrillSize().x),2.2)
            for other in self.board.GetFootprints():
                if other.GetReference()==fp.GetReference():continue
                for other_pad in other.Pads():
                    bounds=other_pad.GetBoundingBox()
                    x0,y0=pcbnew.ToMM(bounds.GetPosition())
                    x1,y1=pcbnew.ToMM(bounds.GetEnd())
                    dx=max(x0-x,0,x-x1);dy=max(y0-y,0,y-y1)
                    self.assertGreaterEqual(math.hypot(dx,dy),3,f'H{i}: hardware overlaps {other.GetReference()} pad')
            # Independently test actual track/via distance, not just rule-area count.
            for item in self.board.GetTracks():
                a=pcbnew.ToMM(item.GetStart());b=pcbnew.ToMM(item.GetEnd())
                dx,dy=b[0]-a[0],b[1]-a[1]
                t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
                dist=math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
                width=item.GetWidth(pcbnew.F_Cu) if item.GetClass()=='PCB_VIA' else item.GetWidth()
                self.assertGreaterEqual(dist-pcbnew.ToMM(width)/2,2.995,f'H{i}: screw copper clearance')

    def test_probe_pads_are_connected_bare_copper(self):
        for ref,net,x,y in TEST_POINTS:
            fp=self.footprints[ref];pad=list(fp.Pads())[0]
            self.assertEqual(pad.GetNetname(),'/'+net)
            self.assertTrue(pad.IsOnLayer(pcbnew.B_Cu))
            self.assertTrue(pad.IsOnLayer(pcbnew.B_Mask))
            self.assertFalse(pad.IsOnLayer(pcbnew.B_Paste))
            self.assertFalse(pad.IsOnLayer(pcbnew.F_Cu))
            self.assertEqual(len(fp.Models()),0)


if __name__=='__main__':unittest.main()
