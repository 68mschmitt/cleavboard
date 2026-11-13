"""Independent checks for sockets, module parity, entry holes and pin depth."""
import unittest
import pcbnew
from design import ROOT, components, read_keys
from socket_interface import validate_interface


class SocketInterfaceTests(unittest.TestCase):
    def board(self):return pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))

    def test_geometry_and_mating_depth(self):
        report=validate_interface(self.board())
        self.assertEqual(len(report['pin_map']),40)
        self.assertAlmostEqual(report['minimum_depth_beyond_contact_point_mm'],1.6)
        self.assertAlmostEqual(report['minimum_pin_tip_to_socket_far_end_mm'],.18)
        self.assertFalse(report['preheadered_waveshare_20808_qualified'])
        self.assertFalse(report['physical_mating_tested'])

    def test_all_module_pins_reach_correct_socket_contact(self):
        parts={p['ref']:p for p in components(*read_keys())}
        report=validate_interface(self.board())
        for row in report['pin_map']:
            expected=parts['U1']['pins'][str(row['module_pin'])]
            self.assertEqual(row['net'].lstrip('/'),expected)
            self.assertEqual(parts[row['socket']]['pins'][str(row['socket_pin'])],expected)
        self.assertEqual(next(r['net'] for r in report['pin_map'] if r['module_pin']==40),'/RAW_USB_5V')

    def test_rejects_wrong_stagger(self):
        board=self.board()
        fp=next(f for f in board.GetFootprints() if f.GetReference()=='J1')
        fp.FindPadByNumber('1').Move(pcbnew.VECTOR2I(0,pcbnew.FromMM(.1)))
        with self.assertRaises(AssertionError):validate_interface(board)

    def test_rejects_plated_entry_hole(self):
        board=self.board()
        fp=next(f for f in board.GetFootprints() if f.GetReference()=='J2')
        hole=next(p for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH)
        hole.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        with self.assertRaises(AssertionError):validate_interface(board)


if __name__=='__main__':unittest.main()
