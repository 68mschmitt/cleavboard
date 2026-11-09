"""Assembly regressions: physical side, socket origins, holes and probe pads."""
import math
import unittest
import pcbnew
from design import ROOT, BOARD_H, MOUNTING_HOLES, TEST_POINTS, read_keys
from export_manufacturing import assembly_rows


class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board=pcbnew.LoadBoard(str(ROOT/'kicad/Cleaver.kicad_pcb'))
        cls.footprints={fp.GetReference():fp for fp in cls.board.GetFootprints()}

    def test_all_populated_smd_bottom_with_socket_centroids(self):
        groups,rows,pads=assembly_rows(self.board)
        self.assertEqual(len(rows),478)
        self.assertEqual(len(groups),12)
        self.assertEqual(sum(len(refs) for refs in groups.values()),478)
        byref={row[0]:row for row in rows}
        self.assertTrue(all(row[3]=='bottom' for row in rows))
        self.assertFalse(set(byref)&{'U1','C5','TP1','TP2','TP3','TP4','TP5','TP6'})
        for key in read_keys()[0]:
            row=byref[key['ref']]
            self.assertAlmostEqual(float(row[1]),key['x']-.635,places=5)
            self.assertAlmostEqual(float(row[2]),BOARD_H-key['y']+3.81,places=5)
        self.assertEqual(self.footprints['U1'].GetLayer(),pcbnew.F_Cu)
        self.assertEqual(self.footprints['C5'].GetLayer(),pcbnew.F_Cu)

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
