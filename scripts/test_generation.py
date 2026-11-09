"""Geometry and router-boundary regression tests (KiCad Python required)."""
import re
import tempfile
import unittest
from pathlib import Path

import pcbnew

from design import ROOT
from generate_kicad import prepare_dsn


class GenerationTests(unittest.TestCase):
    def test_reverse_mount_led_geometry(self):
        board = pcbnew.BOARD()
        fp = pcbnew.FootprintLoad(str(ROOT/'kicad/Cleaver.pretty'), 'MINI_E')
        fp.SetPosition(pcbnew.VECTOR2I(0,0)); board.Add(fp)
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        expected = {'3':(-3.05,-.75),'4':(-3.05,.75),
                    '1':(3.05,.75),'2':(3.05,-.75)}
        for pad in fp.Pads():
            actual = pcbnew.ToMM(pad.GetPosition())
            self.assertAlmostEqual(actual[0],expected[pad.GetNumber()][0],places=5)
            self.assertAlmostEqual(actual[1],expected[pad.GetNumber()][1],places=5)
            self.assertTrue(pad.IsOnLayer(pcbnew.B_Cu))
        self.assertEqual(sum(p.GetLayer()==pcbnew.Edge_Cuts for p in fp.GraphicalItems()),1)

    def dsn(self, existing_power_class=False, count=117):
        power = '/GND /LED_5V /FUSED_5V /RAW_USB_5V'
        text = '''(pcb test (structure
    (boundary (path pcb 0 0 0 100000 0 100000 -100000 0 -100000 0 0))
'''
        text += '\n'.join('(keepout "" (polygon signal 0 1000 -1000 4600 -1000 4600 -4200 1000 -4200 1000 -1000))' for _ in range(count))
        text += '\n    (rule (width 200) (clearance 200)))\n  (network\n'
        text += '    (class kicad_default /SIGNAL ' + ('' if existing_power_class else power) + '''
      (circuit (use_via "Via[0-3]_600:300_um"))
      (rule (width 200) (clearance 200))
    )
'''
        if existing_power_class:
            text += '    (class USB_LED_Power ' + power + '''
      (circuit (use_via "Via[0-3]_800:400_um"))
      (rule (width 600) (clearance 200))
    )
'''
        return text + '  ))\n'

    def prepare(self, text):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode') as directory:
            path = Path(directory)/'test.dsn'; path.write_text(text)
            prepare_dsn(path)
            return path.read_text()

    def test_dsn_fresh_board_rules(self):
        text = self.prepare(self.dsn())
        self.assertIn('(boundary (path pcb 0 325 -325 99675 -325',text)
        self.assertIn('(polygon signal 0 675 -4525 4925 -4525',text)
        self.assertIn('(class board_planes /GND /LED_5V',text)
        self.assertIn('(class usb_led_power /RAW_USB_5V /FUSED_5V',text)
        self.assertIn('(width 300)',text)
        header = re.search(r'\(class kicad_default(.*?)\(circuit',text,re.S).group(1)
        self.assertEqual(header.split(),['/SIGNAL'])

    def test_dsn_saved_board_netclasses(self):
        text = self.prepare(self.dsn(existing_power_class=True))
        self.assertNotIn('(class USB_LED_Power',text)
        self.assertEqual(text.count('(class board_planes'),1)
        self.assertEqual(text.count('(class usb_led_power'),1)

    def test_dsn_rejects_missing_opening(self):
        with self.assertRaisesRegex(ValueError,'Expected 117'):
            self.prepare(self.dsn(count=116))


if __name__=='__main__':
    unittest.main()
