"""Single source of truth for the Cleaver electrical and physical mapping.

YD-RP2040 pin numbers follow the manufacturer's 40-pin drawing, NOT a Pico
symbol. Pin 40 is diode-protected Vout; 35 and 37 are GP29 and GP23.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT.parents[1] / "assets/layout"
U = 19.05
BOARD_W, BOARD_H = 452.4375, 147.6375
ROW_GPIOS = [f"GP{i}" for i in range(8)]
COL_GPIOS = [f"GP{i}" for i in range(8, 23)] + ["GP26"]
RGB_GPIO, POWER_GPIO = "GP27", "GP28"
MODULE_X, MODULE_Y = BOARD_W - 26.67, 13.39
# M2 clearance holes; reserve a 6 mm diameter for heads, washers and standoffs.
# Coordinates are top-view millimetres from the PCB's upper-left corner.
MOUNTING_HOLES = [(4, 4), (110, 23.8), (220, 23.8), (330, 23.8),
                  (395, 26), (313, 70), (4, 143), (90, 138),
                  (220, 138), (365, 138), (448, 138)]
FIDUCIALS = [(20, 24), (360, 138), (395, 2)]
TEST_POINTS = [('TP2', 'GND', 410, 27), ('TP3', 'RAW_USB_5V', 418, 27),
               ('TP4', 'LED_5V', 426, 27), ('TP5', 'LED_EN', 434, 27),
               ('TP6', 'RGB_BUFFERED', 402, 27)]
MODULE_PINS = {
    1: "GP0", 2: "GP1", 3: "GND", 4: "GP2", 5: "GP3", 6: "GP4",
    7: "GP5", 8: "GND", 9: "GP6", 10: "GP7", 11: "GP8", 12: "GP9",
    13: "GND", 14: "GP10", 15: "GP11", 16: "GP12", 17: "GP13",
    18: "GND", 19: "GP14", 20: "GP15", 21: "GP16", 22: "GP17",
    23: "GND", 24: "GP18", 25: "GP19", 26: "GP20", 27: "GP21",
    28: "GND", 29: "GP22", 30: "RUN", 31: "GP26", 32: "GP27",
    33: "GND", 34: "GP28", 35: "GP29", 36: "3V3_OUT", 37: "GP23",
    38: "GND", 39: "VIN", 40: "VOUT",
}
GPIO_PIN = {name: pin for pin, name in MODULE_PINS.items() if name.startswith("GP")}


def read_keys():
    keys = []
    ybase = ycarry = 0.0
    for row_index, row in enumerate(json.loads((INPUT / "keyboard-layout.json").read_text())):
        x, geom = 0.0, {}
        for item in row:
            if isinstance(item, dict):
                geom.update(item)
                x += float(item.get("x", 0))
                ycarry += float(item.get("y", 0))
                continue
            w, h = float(geom.get("w", 1)), float(geom.get("h", 1))
            if not geom.get("d", False):
                i = len(keys)
                keys.append(dict(
                    ref=f"SW{i + 1:03d}", diode=f"D{i + 1:03d}",
                    led_ref=f"LED{i + 1:03d}", cap_ref=f"C{i + 101}",
                    legend=(item or "Space").replace("\n", "/"),
                    x=(x + w / 2) * U, y=(ybase + ycarry + h / 2) * U,
                    w=w, h=h, kle_row=row_index, matrix_row=i // 16,
                    matrix_col=i % 16, key_net=f"KEY{i:03d}",
                ))
            x += w
            geom = {}
        ybase += 1
    leds = []
    for r in range(7):
        leds.extend(sorted((k for k in keys if k["kle_row"] == r),
                           key=lambda k: k["x"], reverse=not bool(r % 2)))
    for i, k in enumerate(leds):
        k.update(led_index=i, rgb_in=f"RGB_{i:03d}",
                 rgb_out=f"RGB_{i + 1:03d}" if i < len(leds) - 1 else None)
    validate_keys(keys, leds)
    return keys, leds


def validate_keys(keys, leds):
    if len(keys) != 117 or len(leds) != 117:
        raise ValueError("Expected exactly 117 switches and LEDs")
    cells = [(k["matrix_row"], k["matrix_col"]) for k in keys]
    if len(set(cells)) != len(cells):
        raise ValueError("Duplicate matrix addresses: keys would be indistinguishable")
    if any(not (0 <= r < 8 and 0 <= c < 16) for r, c in cells):
        raise ValueError("Matrix address outside 8x16")
    gpios = ROW_GPIOS + COL_GPIOS + [RGB_GPIO, POWER_GPIO]
    if len(gpios) != len(set(gpios)) or any(g not in GPIO_PIN for g in gpios):
        raise ValueError("GPIO conflict or pin absent from YD-RP2040 headers")
    if {k["ref"] for k in keys} != {k["ref"] for k in leds}:
        raise ValueError("RGB chain does not cover every key exactly once")
    if sorted(k["led_index"] for k in leds) != list(range(117)):
        raise ValueError("RGB indices are not a permutation of 0..116")


def components(keys, leds):
    """Schematic and board share these exact pin-to-net assignments."""
    result = []

    def add(ref, kind, value, x, y, pins, *, back=False, angle=0):
        result.append(dict(ref=ref, kind=kind, value=value, x=x, y=y,
                           pins={str(p): n for p, n in pins.items()}, back=back, angle=angle))

    module = {p: None for p in MODULE_PINS}
    for r, gpio in enumerate(ROW_GPIOS):
        module[GPIO_PIN[gpio]] = f"ROW{r}"
    for c, gpio in enumerate(COL_GPIOS):
        module[GPIO_PIN[gpio]] = f"COL{c:02d}"
    module.update({p: "GND" for p, name in MODULE_PINS.items() if name == "GND"})
    module.update({GPIO_PIN[RGB_GPIO]: "RGB_DATA", GPIO_PIN[POWER_GPIO]: "LED_EN"})
    add("U1", "YD_RP2040", "YD-RP2040 4MB USB-C", MODULE_X, MODULE_Y, module, angle=-90)
    for k in keys:
        x, y = k["x"], k["y"]
        add(k["ref"], "MX", "CPG151101S11-16", x, y,
            {1: f"ROW{k['matrix_row']}", 2: k["key_net"]}, back=True)
        result[-1]['key_label'] = k['legend']
        # Standard SOD-123 numbering: 1=cathode, 2=anode.
        # Leave ~0.36 mm nominal body gap to the socket (was only ~0.11 mm).
        add(k["diode"], "D_SOD123", "1N4148W", x, y - 8.25,
            {1: f"COL{k['matrix_col']:02d}", 2: k["key_net"]}, back=True)
        add(k["led_ref"], "MINI_E", "SK6812MINI-E C5149201", x, y + 5.08,
            {3: "LED_5V", 4: k["rgb_out"], 1: "GND", 2: k["rgb_in"]}, back=True)
        add(k["cap_ref"], "C_0805", "100nF 50V X7R", x + 5.8, y + 5.08,
            {1: "LED_5V", 2: "GND"}, back=True)
    # User-approved short wire from raw USB VBUS, BEFORE the module's BAT54C.
    # Pin 40 stays unused: never send the RGB load through that small diode.
    add("TP1", "WirePad", "USB VBUS TAP +5V", 446, 27, {1: "RAW_USB_5V"}, back=True)
    # No mechanical switch. GP28 controls the protected RGB branch in firmware.
    add("F1", "PTC_1206", "1206L050YR 0.50A hold", 393, 4.5,
        {1: "RAW_USB_5V", 2: "FUSED_5V"})
    add("U3", "TPS2553", "TPS2553DBVR", 390, 14,
        {1: "FUSED_5V", 2: "GND", 3: "LED_EN", 4: None, 5: "CURRENT_LIMIT", 6: "LED_5V"})
    add("U2", "LV1T125", "SN74LV1T125DBVR", 382, 19,
        {1: "GND", 2: "RGB_DATA", 3: "GND", 4: "RGB_BUFFERED", 5: "LED_5V"})
    add("R1", "R_0805", "330R", 375, 21, {1: "RGB_BUFFERED", 2: "RGB_000"})
    add("R2", "R_0805", "100k", 384, 10, {1: "LED_EN", 2: "GND"})
    add("R3", "R_0805", "100k", 377, 25, {1: "RGB_DATA", 2: "GND"})
    add("C1", "C_0805", "1uF 50V X7R", 394, 8, {1: "FUSED_5V", 2: "GND"})
    add("C2", "C_0805", "22uF 10V X5R", 395, 14, {1: "LED_5V", 2: "GND"})
    add("C3", "C_0805", "100nF 50V X7R", 386, 23, {1: "LED_5V", 2: "GND"})
    add("R4", "R_0805", "75k 1%", 393, 17, {1: "CURRENT_LIMIT", 2: "GND"})
    # Downstream of the current limiter, not directly across USB: absorbs
    # coincident LED PWM pulses without tripping the 350mA input-current limit.
    add("C5", "C_PCF_D10", "470uF 10V PCF1A471MCL1GS", 377, 6,
        {1: "LED_5V", 2: "GND"}, back=True)
    for part in result:
        if part['ref'] in ('F1', 'U2', 'U3', 'R1', 'R2', 'R3', 'R4', 'C1', 'C2', 'C3'):
            part['back'] = True
    for ref, net, x, y in TEST_POINTS:
        add(ref, 'TestPad', net, x, y, {1: net}, back=True)
    return result


def default_keycodes(keys):
    """KLE order, including distinct left/right modifiers and numpad keycodes."""
    first = ["KC_ESC"] + [f"KC_F{i}" for i in range(1, 13)] + ["KC_PSCR", "KC_SCRL", "KC_PAUS"]
    rows = [first,
        ["KC_F13", "KC_GRV"] + [f"KC_{i}" for i in range(1, 10)] +
        ["KC_0", "KC_MINS", "KC_EQL", "KC_BSPC", "KC_INS", "KC_HOME", "KC_PGUP", "KC_NUM", "KC_PSLS", "KC_PAST", "KC_PMNS"],
        ["KC_F14", "KC_TAB"] + [f"KC_{v}" for v in "QWERTYUIOP"] +
        ["KC_LBRC", "KC_RBRC", "KC_BSLS", "KC_DEL", "KC_END", "KC_PGDN", "KC_P7", "KC_P8", "KC_P9", "KC_PPLS"],
        ["KC_F15", "KC_CAPS"] + [f"KC_{v}" for v in "ASDFGHJKL"] +
        ["KC_SCLN", "KC_QUOT", "KC_ENT", "KC_P4", "KC_P5", "KC_P6"],
        ["KC_F16", "KC_LSFT"] + [f"KC_{v}" for v in "ZXCVBNM"] +
        ["KC_COMM", "KC_DOT", "KC_SLSH", "KC_RSFT", "KC_F23", "KC_UP", "KC_F24", "KC_P1", "KC_P2", "KC_P3", "KC_PENT"],
        ["KC_F17", "KC_LCTL", "KC_LGUI", "KC_LALT", "KC_SPC", "KC_RALT", "KC_RGUI", "KC_APP", "KC_RCTL", "KC_LEFT", "KC_DOWN", "KC_RGHT", "KC_P0", "KC_PDOT"],
        ["KC_F18", "KC_F19", "KC_F20", "KC_F21", "KC_F22", "KC_CALC"]]
    flat = [code for row in rows for code in row]
    assert len(flat) == len(keys) == 117
    return flat
