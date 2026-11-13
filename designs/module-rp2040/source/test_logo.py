"""Badge chain, serialized fit, retention, and executable firmware regressions."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import numpy as np
import pcbnew
import trimesh
from shapely import Point, Polygon, box

from build_3d_models import freecad
from design import BOARD_H, ROOT, REVISION
from generate_case import Parameters, badge_shapes, prism
from generate_top_plate import top_surface


class LogoTests(unittest.TestCase):
    def test_chain_starts_after_last_key_and_uses_protected_supply(self):
        board = pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
        fps = {f.GetReference(): f for f in board.GetFootprints()}
        previous = fps['LED112'].FindPadByNumber('4')
        for index, (x, y) in enumerate([(223.3975, 135.6125), (231.8975, 135.6125),
                                       (231.8975, 140.6125), (223.3975, 140.6125)], 118):
            led = fps[f'LED{index}']
            np.testing.assert_allclose(pcbnew.ToMM(led.GetPosition()), [x, y], atol=1e-6, rtol=0)
            self.assertEqual(previous.GetNetname(), led.FindPadByNumber('2').GetNetname())
            self.assertEqual(led.FindPadByNumber('3').GetNetname(), '/LED_5V')
            self.assertEqual(led.FindPadByNumber('1').GetNetname(), '/GND')
            self.assertEqual(led.GetLayer(), pcbnew.B_Cu)
            cap = fps[f'C{index+100}']
            self.assertEqual(cap.FindPadByNumber('1').GetNetname(), '/LED_5V')
            self.assertEqual(cap.FindPadByNumber('2').GetNetname(), '/GND')
            previous = led.FindPadByNumber('4')
        self.assertTrue(previous.GetNetname().startswith('unconnected-'))
        self.assertEqual(tuple(pcbnew.ToMM(fps['H9'].GetPosition())), (250., 138.))

    def test_serialized_aperture_is_centered_between_the_two_trios(self):
        board = pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
        fps = {f.GetReference(): f for f in board.GetFootprints()}
        left = pcbnew.ToMM(fps['SW114'].GetPosition())  # M8
        right = pcbnew.ToMM(fps['SW115'].GetPosition())  # M9
        center = ((left[0]+right[0])/2, BOARD_H-left[1])
        plate = trimesh.load_mesh(ROOT/f'mechanical/rev{REVISION}/Cleaver-top-plate-rev{REVISION}.stl')
        holes = [Polygon(r) for r in top_surface(plate, 1.5).interiors]
        hole = next(h for h in holes if h.contains(Point(*center)))
        np.testing.assert_allclose(hole.bounds, [center[0]-8.2, center[1]-8.2,
                                               center[0]+8.2, center[1]+8.2], rtol=0, atol=2e-5)
        self.assertGreater(hole.bounds[1], 1.3)
        _, part = freecad()
        cover = part.read(str(ROOT/f'mechanical/rev{REVISION}/case/Cleaver-case-top-cover-rev{REVISION}.step'))
        gauge = prism(box(center[0]-8.199, left[1]-8.199, center[0]+8.199, left[1]+8.199), 8.4, 2.4)
        self.assertLess(cover.common(gauge).Volume, 1e-6)

    def test_insert_cannot_escape_up_or_down_with_cover_installed(self):
        app, part = freecad()
        out = ROOT/f'mechanical/rev{REVISION}/case'
        carrier = part.read(str(out/'Logo-light-well.step'))
        insert = part.read(str(out/'Logo-insert-blank.step'))
        cover = part.read(str(out/f'Cleaver-case-top-cover-rev{REVISION}.step'))
        self.assertLess(carrier.common(insert).Volume, 1e-6)
        self.assertLess(cover.common(insert).Volume, 1e-6)
        up, down = insert.copy(), insert.copy()
        up.translate(app.Vector(0, 0, .3))
        down.translate(app.Vector(0, 0, -.3))
        self.assertGreater(cover.common(up).Volume, 1)
        self.assertGreater(carrier.common(down).Volume, 1)
        p = Parameters(**json.loads((out/'parameters.json').read_text()))
        for saved, expected in zip((carrier, insert), badge_shapes(p)):
            self.assertAlmostEqual(saved.Volume, expected.Volume, places=5)
        report = json.loads((out/'validation.json').read_text())['fit_checks']['logo']
        self.assertTrue(report['four_optical_paths_clear'])
        self.assertEqual(report['diffuser_thickness_mm'], 1.)

    @unittest.skipUnless(shutil.which('cc'), 'Firmware callback checks require a host C compiler')
    def test_actual_firmware_callbacks_brightness_direct_mode_and_usb_gating(self):
        # Compile the actual keyboard source with a tiny QMK boundary stub.
        # Exercise range boundaries and hostile stored brightness as well as
        # independent Vial colours; target builds separately verify real APIs.
        header = '''#pragma once
#include <stdbool.h>
#include <stdint.h>
#define GP28 28
#include "config.h"
#define RGB_MATRIX_MAXIMUM_BRIGHTNESS 8
#define RGB_MATRIX_VIALRGB_DIRECT 99
#define USB_DEVICE_STATE_CONFIGURED 1
typedef struct { uint8_t h,s,v; } HSV;
typedef struct { uint8_t r,g,b; } RGB;
typedef struct { bool caps_lock,num_lock,scroll_lock; } led_t;
void setPinOutput(int); void writePinLow(int); void writePinHigh(int); void wait_ms(int);
void keyboard_pre_init_user(void); void housekeeping_task_user(void);
void suspend_power_down_user(void); void suspend_wakeup_init_user(void);
int usb_device_state_get_configure_state(void);
bool rgb_matrix_is_enabled(void); bool rgb_matrix_get_suspend_state(void);
bool rgb_matrix_indicators_advanced_user(uint8_t,uint8_t);
HSV rgb_matrix_get_hsv(void); uint8_t rgb_matrix_get_mode(void);
RGB hsv_to_rgb(HSV); void rgb_matrix_set_color(int,uint8_t,uint8_t,uint8_t);
led_t host_keyboard_led_state(void);
'''
        harness = '''#include "stub.h"
#include <assert.h>
#include <string.h>
static int pin,usb,mode; static bool enabled=true,suspended,user=true;
static HSV hsv={0,0,8}; static unsigned calls[121]; static RGB pixels[121];
HSV g_direct_mode_colors[121];
void setPinOutput(int p){} void writePinLow(int p){pin=0;} void writePinHigh(int p){pin=1;}
void wait_ms(int n){} void keyboard_pre_init_user(void){} void housekeeping_task_user(void){}
void suspend_power_down_user(void){} void suspend_wakeup_init_user(void){}
int usb_device_state_get_configure_state(void){return usb;}
bool rgb_matrix_is_enabled(void){return enabled;}
bool rgb_matrix_get_suspend_state(void){return suspended;}
bool rgb_matrix_indicators_advanced_user(uint8_t a,uint8_t b){return user;}
HSV rgb_matrix_get_hsv(void){return hsv;} uint8_t rgb_matrix_get_mode(void){return mode;}
RGB hsv_to_rgb(HSV h){return (RGB){h.v,h.v,h.v};}
void rgb_matrix_set_color(int i,uint8_t r,uint8_t g,uint8_t b){assert(i>=0 && i<121); calls[i]++; pixels[i]=(RGB){r,g,b};}
led_t host_keyboard_led_state(void){return (led_t){0};}
extern void keyboard_pre_init_kb(void),housekeeping_task_kb(void),suspend_power_down_kb(void);
extern bool rgb_matrix_indicators_advanced_kb(uint8_t,uint8_t);
int main(void){
    keyboard_pre_init_kb(); housekeeping_task_kb(); assert(pin==0);
    usb=1; housekeeping_task_kb(); assert(pin==1);
    enabled=false; housekeeping_task_kb(); assert(pin==0);
    enabled=true; housekeeping_task_kb(); assert(pin==1);
    suspended=true; housekeeping_task_kb(); assert(pin==0);
    suspended=false; housekeeping_task_kb(); assert(pin==1);
    suspend_power_down_kb(); assert(pin==0);
    rgb_matrix_indicators_advanced_kb(0,117);
    for(int i=0;i<121;i++) assert(calls[i]==0);
    rgb_matrix_indicators_advanced_kb(118,120);
    assert(!calls[117] && calls[118]==1 && calls[119]==1 && !calls[120]);
    assert(pixels[118].r==32);
    hsv.v=0; rgb_matrix_indicators_advanced_kb(117,121); assert(pixels[120].r==0);
    hsv.v=255; rgb_matrix_indicators_advanced_kb(117,121); assert(pixels[120].r==32);
    hsv.v=2; rgb_matrix_indicators_advanced_kb(117,121); assert(pixels[120].r==8);
#ifdef VIALRGB_ENABLE
    mode=RGB_MATRIX_VIALRGB_DIRECT;
    for(int i=117;i<121;i++) g_direct_mode_colors[i]=(HSV){0,0,i-117};
    rgb_matrix_indicators_advanced_kb(117,121);
    assert(pixels[117].r==0 && pixels[118].r==4 && pixels[119].r==8 && pixels[120].r==12);
#endif
    memset(calls,0,sizeof calls); user=false;
    assert(!rgb_matrix_indicators_advanced_kb(0,121));
    for(int i=0;i<121;i++) assert(calls[i]==0);
    return 0;
}
'''
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='cleaver-logo-test-') as temp:
            folder = Path(temp)
            (folder/'stub.h').write_text(header)
            (folder/'main.c').write_text(harness)
            for name in ('usb_device_state.h', 'color.h'):
                (folder/name).write_text('#include "stub.h"\n')
            for variant in ([], ['-DVIALRGB_ENABLE']):
                subprocess.run(['cc', '-std=c11', '-Werror=implicit-function-declaration',
                                '-DQMK_KEYBOARD_H="stub.h"', *variant, '-I'+str(folder),
                                '-I'+str(ROOT/'firmware'), str(ROOT/'firmware/cleaver.c'),
                                str(folder/'main.c'), '-o', str(folder/'check')], check=True)
                subprocess.run([str(folder/'check')], check=True)


if __name__ == '__main__':
    unittest.main()
