"""Run with python3 -B -m unittest discover -s scripts -p 'test_*.py'."""
import copy
import csv
import json
import unittest

from design import (ROOT, MODULE_PINS, ROW_GPIOS, COL_GPIOS, GPIO_PIN,
                    read_keys, validate_keys, components, default_keycodes)


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.keys, self.leds = read_keys()

    def test_unique_matrix(self):
        self.assertEqual(len(self.keys), 117)
        self.assertEqual(len({(k['matrix_row'],k['matrix_col']) for k in self.keys}), 117)

    def test_duplicate_is_rejected(self):
        keys = copy.deepcopy(self.keys)
        keys[1]['matrix_row'] = keys[0]['matrix_row']
        keys[1]['matrix_col'] = keys[0]['matrix_col']
        with self.assertRaisesRegex(ValueError, 'Duplicate matrix'):
            validate_keys(keys, self.leds)

    def test_module_is_not_pico_pinout(self):
        self.assertEqual([MODULE_PINS[p] for p in (35,36,37,38,39,40)],
                         ['GP29','3V3_OUT','GP23','GND','VIN','VOUT'])
        self.assertEqual(len(set(ROW_GPIOS + COL_GPIOS + ['GP27','GP28'])),26)

    def test_diode_direction_and_module_connections(self):
        parts = {p['ref']:p for p in components(self.keys,self.leds)}
        for k in self.keys:
            self.assertEqual(parts[k['diode']]['pins']['1'], f"COL{k['matrix_col']:02d}")
            self.assertEqual(parts[k['diode']]['pins']['2'], k['key_net'])
        self.assertEqual(parts['U1']['pins'][str(GPIO_PIN['GP27'])], 'RGB_DATA')
        self.assertEqual(parts['U1']['pins']['36'], None)
        self.assertEqual(parts['U1']['pins']['38'], 'GND')

    def test_rgb_chain(self):
        for i,k in enumerate(self.leds):
            self.assertEqual(k['rgb_in'], f'RGB_{i:03d}')
            self.assertEqual(k['rgb_out'], f'RGB_{i+1:03d}' if i<116 else None)

    def test_usb_tap_bypasses_module_diode(self):
        parts = {p['ref']:p for p in components(self.keys,self.leds)}
        self.assertIsNone(parts['U1']['pins']['40'])
        self.assertEqual(parts['TP1']['pins']['1'], 'RAW_USB_5V')
        self.assertEqual(parts['F1']['pins']['1'], 'RAW_USB_5V')
        self.assertEqual(parts['U3']['pins']['1'], 'FUSED_5V')
        self.assertEqual(parts['U3']['pins']['6'], 'LED_5V')
        self.assertEqual(parts['R4']['value'], '75k 1%')
        self.assertEqual(sum(p['kind']=='C_0805' for p in parts.values()), 120)

    def test_generated_firmware_and_csv(self):
        fw = ROOT/'kicad/firmware'
        info = json.loads((fw/'keyboard.json').read_text())
        layout = info['layouts']['LAYOUT']['layout']
        self.assertEqual([v['matrix'] for v in layout], [[k['matrix_row'],k['matrix_col']] for k in self.keys])
        rgb = info['rgb_matrix']['layout']
        self.assertEqual([v['matrix'] for v in rgb], [[k['matrix_row'],k['matrix_col']] for k in self.leds])
        with (fw/'key_matrix.csv').open(newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows),117)
        self.assertTrue(all(None not in row for row in rows))
        self.assertEqual(rows[86]['legend'],self.keys[86]['legend'])
        self.assertEqual(len(default_keycodes(self.keys)),117)


if __name__ == '__main__':
    unittest.main()
