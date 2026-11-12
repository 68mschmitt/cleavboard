"""Offline model coverage and non-destructive assignment regressions."""
import json
import unittest

import pcbnew

from design import ROOT
from models_3d import (MODELS, PREFIX, form_end, replace_models,
                       validate_models, without_models)


class ModelTests(unittest.TestCase):
    def test_board_model_coverage(self):
        board = pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
        result = validate_models(board)
        self.assertEqual(result['model_instances'],597)
        self.assertEqual(result['populated_footprints'],480)

    def test_library_model_coverage_and_mounting(self):
        for name,files in MODELS.items():
            board = pcbnew.BOARD()
            fp = pcbnew.FootprintLoad(str(ROOT/'Cleaver.pretty'),name)
            self.assertIsNotNone(fp)
            board.Add(fp)
            self.assertEqual([m.m_Filename for m in fp.Models()],[PREFIX+f for f in files])
            # KiCad handles bottom-side mirroring; do not introduce a second
            # manual flip into the model itself when regenerating placement.
            fp.Flip(fp.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            self.assertEqual(len(fp.Models()),len(files))
            for model in fp.Models():
                self.assertEqual(tuple(getattr(model.m_Rotation,a) for a in ('x','y','z')),(0,0,0))

    def test_model_file_headers_and_step_counterparts(self):
        folder = ROOT/'Cleaver.3dshapes'
        for filename in {f for files in MODELS.values() for f in files}:
            path = folder/filename
            self.assertTrue(path.read_text().startswith('#VRML V2.0 utf8'),filename)
            self.assertTrue(path.with_suffix('.step').read_text().startswith('ISO-10303-21;'),filename)

    def test_assignment_is_model_only_and_idempotent(self):
        original = '(module MINI_E (layer F.Cu)\n  (descr "text with \\"quotes\\" and (brackets)")\n  (pad 1 smd rect (at 2 3) (size 1 1) (layers F.Cu))\n)\n'
        assigned = replace_models(original,'MINI_E')
        self.assertEqual(without_models(assigned),original)
        self.assertEqual(replace_models(assigned,'MINI_E'),assigned)
        self.assertEqual(form_end(original,0),len(original)-1)

    def test_unfamiliar_assignment_is_preserved(self):
        for filename in ('"my-model.step"','my-model.step'):
            text = '(module MINI_E\n  (model '+filename+' (offset (xyz 0 0 1)))\n)\n'
            with self.assertRaisesRegex(ValueError,'unfamiliar'):
                replace_models(text,'MINI_E')

    def test_bare_wire_pad_has_no_invented_connector(self):
        self.assertEqual(MODELS['WirePad'],())
        self.assertEqual(len(MODELS['Kailh_socket_MX']),2)

    def test_generated_model_envelopes(self):
        data = json.loads((ROOT/'Cleaver.3dshapes/generated.json').read_text())
        module = json.loads((ROOT/'Cleaver.3dshapes/generated-rp2040-plus.json').read_text())['Waveshare_RP2040_Plus_Approx']['bounds_mm']
        self.assertAlmostEqual(module[3]-module[0],21,places=4)
        self.assertAlmostEqual(module[1],-25.5,places=4)
        self.assertGreater(module[4],25.5)  # USB shell projects out of the PCB.
        led = data['LED_SK6812MINI-E_Reverse']['bounds_mm']
        self.assertAlmostEqual(led[3]-led[0],5.88,places=4)
        self.assertLess(led[2],0)  # Emitter is inside the board opening, not upside down.
        self.assertGreater(led[5],0)


if __name__=='__main__':
    unittest.main()
