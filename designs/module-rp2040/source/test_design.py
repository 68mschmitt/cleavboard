"""Run with python3 -B -m unittest discover -s scripts -p 'test_*.py'."""
import copy
import csv
import json
import re
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

    def test_waveshare_pico_compatible_pinout(self):
        self.assertEqual([MODULE_PINS[p] for p in (35,36,37,38,39,40)],
                         ['ADC_VREF','3V3_OUT','3V3_EN','GND','VSYS','VBUS'])
        self.assertEqual(len(set(ROW_GPIOS + COL_GPIOS + ['GP27','GP28'])),26)

    def test_diode_direction_and_module_connections(self):
        parts = {p['ref']:p for p in components(self.keys,self.leds)}
        for k in self.keys:
            self.assertEqual(parts[k['diode']]['pins']['1'], f"COL{k['matrix_col']:02d}")
            self.assertEqual(parts[k['diode']]['pins']['2'], k['key_net'])
        self.assertEqual(parts['U1']['pins'][str(GPIO_PIN['GP27'])], 'RGB_DATA')
        self.assertEqual(parts['U1']['pins']['36'], 'MODULE_3V3_OUT')
        self.assertEqual(parts['U1']['pins']['38'], 'GND')

    def test_rgb_chain(self):
        for i,k in enumerate(self.leds):
            self.assertEqual(k['rgb_in'], f'RGB_{i:03d}')
            self.assertEqual(k['rgb_out'], f'RGB_{i+1:03d}' if i<116 else None)

    def test_vbus_header_feeds_protected_led_branch(self):
        parts = {p['ref']:p for p in components(self.keys,self.leds)}
        self.assertEqual(parts['U1']['pins']['40'], 'RAW_USB_5V')
        for n in ('35','36','37','39'):
            self.assertEqual(parts['U1']['pins'][n], 'MODULE_'+MODULE_PINS[int(n)])
        self.assertEqual(parts['TP1']['pins']['1'], 'RAW_USB_5V')
        self.assertEqual(parts['F1']['pins']['1'], 'RAW_USB_5V')
        self.assertEqual(parts['U3']['pins']['1'], 'FUSED_5V')
        self.assertEqual(parts['U3']['pins']['6'], 'LED_5V')
        self.assertEqual(parts['R4']['value'], '75k 1%')
        self.assertEqual(sum(p['kind']=='C_0805' for p in parts.values()), 120)

    def test_generated_firmware_and_csv(self):
        fw = ROOT/'firmware'
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

    def test_firmware_gpio_to_waveshare_header_mapping(self):
        # Independent transcription of Waveshare's pinout, not GPIO_PIN.
        header = dict(zip([f'GP{i}' for i in range(23)] + ['GP26','GP27','GP28'],
                          [1,2,4,5,6,7,9,10,11,12,14,15,16,17,19,20,21,22,24,25,26,27,29,31,32,34]))
        info = json.loads((ROOT/'firmware/keyboard.json').read_text())
        module = next(p for p in components(self.keys,self.leds) if p['ref']=='U1')['pins']
        for direction,prefix in [('rows','ROW'),('cols','COL')]:
            for i,gpio in enumerate(info['matrix_pins'][direction]):
                self.assertEqual(module[str(header[gpio])],f'{prefix}{i}' if prefix=='ROW' else f'COL{i:02d}')
        self.assertEqual(module[str(header[info['ws2812']['pin']])],'RGB_DATA')
        config = (ROOT/'firmware/config.h').read_text()
        enable = re.search(r'^#define LED_POWER_PIN (GP\d+)$',config,re.M).group(1)
        self.assertEqual(module[str(header[enable])],'LED_EN')
        self.assertIn('#define WEAR_LEVELING_RP2040_FLASH_SIZE (2 * 1024 * 1024)',config)

    def test_vial_identity_and_secure_unlock_retained(self):
        fw = ROOT/'firmware'
        config = (fw/'keymaps/vial/config.h').read_text()
        info = json.loads((fw/'keyboard.json').read_text())
        vial = json.loads((fw/'keymaps/vial/vial.json').read_text())
        self.assertEqual(vial['vendorId'],info['usb']['vid'])
        self.assertEqual(vial['productId'],info['usb']['pid'])
        self.assertNotIn('VIAL_INSECURE',config)
        def values(name):
            return re.search(r'#define '+name+r' \{ ([^}]+) \}',config).group(1).split(', ')
        self.assertEqual(values('VIAL_KEYBOARD_UID'),['0x48','0x7D','0xA8','0xAD','0xC8','0x69','0x52','0x19'])
        codes = default_keycodes(self.keys)
        cells = [(int(r),int(c)) for r,c in zip(values('VIAL_UNLOCK_COMBO_ROWS'),values('VIAL_UNLOCK_COMBO_COLS'))]
        self.assertEqual(cells,[(k['matrix_row'],k['matrix_col']) for k,code in zip(self.keys,codes) if code in ('KC_ESC','KC_ENT')])
        rules = (fw/'keymaps/vial/rules.mk').read_text()
        for option in ('VIA_ENABLE','VIAL_ENABLE','VIALRGB_ENABLE'):
            self.assertIn(option+' = yes',rules)


if __name__ == '__main__':
    unittest.main()
