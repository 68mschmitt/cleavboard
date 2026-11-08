#!/usr/bin/env python3
"""Generate the Cleaver keyboard KiCad starter project from the supplied KLE/DXF."""

from __future__ import annotations

import json
import math
import re
import shutil
import uuid
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "plate-2026-11-07T22_24_25.197Z"
OUT = ROOT / "kicad"
PRETTY = OUT / "Cleaver.pretty"
NAME = "Cleaver"
ROW_PINS = [f"GP{i}" for i in range(13)]
COL_PINS = [f"GP{i}" for i in range(13, 23)] + ["GP26"]
RGB_PIN = "GP27"


def uid() -> str:
    return str(uuid.uuid4())


def component_uuid(ref: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cleaver-keyboard:{ref}"))


def q(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def read_keys():
    layout = json.loads((INPUT / "keyboard-layout(1).json").read_text())
    keys = []
    ybase = 0.0
    ycarry = 0.0
    for row_index, row in enumerate(layout):
        x = 0.0
        geom = {}
        for item in row:
            if isinstance(item, dict):
                geom.update(item)
                x += float(item.get("x", 0))
                ycarry += float(item.get("y", 0))
                continue
            w = float(geom.get("w", 1))
            h = float(geom.get("h", 1))
            if not geom.get("d", False):
                label = item if item else "Space"
                keys.append({
                    "kle_row": row_index,
                    "legend": label.replace("\n", "/"),
                    "x": (x + w / 2) * 19.05,
                    "y": (ybase + ycarry + h / 2) * 19.05,
                    "w": w,
                    "h": h,
                })
            x += w
            geom = {}
        ybase += 1.0

    if len(keys) != 117:
        raise ValueError(f"Expected 117 switch positions after decal filtering, got {len(keys)}")

    # The electrical matrix is split at 11 switches per row, keeping the original
    # KLE row order. This yields 13 rows x 11 columns (24 GPIOs).
    matrix_row = 0
    for kle_row in range(7):
        group = [k for k in keys if k["kle_row"] == kle_row]
        for start in range(0, len(group), 11):
            for col, key in enumerate(group[start : start + 11]):
                key["matrix_row"] = matrix_row
                key["matrix_col"] = col
            matrix_row += 1
    if matrix_row != 13:
        raise ValueError(f"Expected 13 electrical rows, got {matrix_row}")

    for i, key in enumerate(keys, 1):
        key["ref"] = f"SW{i:03d}"
        key["diode"] = f"D{i:03d}"
        key["key_net"] = f"KEY{i:03d}"
        key["led_ref"] = f"LED{i:03d}"

    # Serpentine LED order follows the physical KLE rows for clean RGB mapping.
    led_order = []
    for kle_row in range(7):
        row_keys = [k for k in keys if k["kle_row"] == kle_row]
        row_keys.sort(key=lambda k: k["x"], reverse=bool(kle_row % 2))
        led_order.extend(row_keys)
    for i, key in enumerate(led_order):
        key["led_index"] = i
        key["rgb_in"] = f"RGB_CHAIN_{i:03d}"
        key["rgb_out"] = f"RGB_CHAIN_{i + 1:03d}"
    return keys, led_order


def write_custom_footprints():
    PRETTY.mkdir(parents=True, exist_ok=True)
    # This is the project's existing, tested Kailh MX hotswap footprint. Keep
    # the upstream license alongside the vendored module.
    socket_fp = PRETTY / "Kailh_socket_MX.kicad_mod"
    socket_license = PRETTY / "LICENSE.md"
    upstream = Path("/home/mschmitt/projects/lots-of-projects/keyswitches.pretty")
    if not socket_fp.exists():
        source = upstream / socket_fp.name
        if not source.exists():
            raise FileNotFoundError("Vendor Kailh_socket_MX.kicad_mod into kicad/Cleaver.pretty first")
        shutil.copyfile(source, socket_fp)
    if not socket_license.exists() and (upstream / socket_license.name).exists():
        shutil.copyfile(upstream / socket_license.name, socket_license)

    (PRETTY / "SK6812MINI-E.kicad_mod").write_text("""(module SK6812MINI-E (layer F.Cu) (tedit 0)
  (descr "SK6812MINI-E addressable RGB LED, pinout 1=VDD 2=DOUT 3=GND 4=DIN")
  (tags "SK6812MINI-E RGB addressable LED")
  (attr smd)
  (fp_text reference REF** (at 0 -3.2) (layer F.SilkS)
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value SK6812MINI-E (at 0 3.2) (layer F.Fab)
    (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.75 -1.85) (end 1.75 1.85) (layer F.Fab) (width 0.1))
  (fp_line (start -1.75 -1.85) (end 1.75 -1.85) (layer F.SilkS) (width 0.12))
  (pad 1 smd rect (at -1 -1) (size 1.1 1.1) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1 -1) (size 1.1 1.1) (layers F.Cu F.Paste F.Mask))
  (pad 3 smd rect (at 1 1) (size 1.1 1.1) (layers F.Cu F.Paste F.Mask))
  (pad 4 smd rect (at -1 1) (size 1.1 1.1) (layers F.Cu F.Paste F.Mask))
)""")

    (PRETTY / "D_SOD-123.kicad_mod").write_text("""(module D_SOD-123 (layer F.Cu) (tedit 0)
  (descr "1N4148W SOD-123 switching diode") (tags "SOD-123 diode") (attr smd)
  (fp_text reference REF** (at 0 -1.8) (layer F.SilkS) (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value D_SOD-123 (at 0 1.8) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.55 -1.05) (end 1.55 1.05) (layer F.Fab) (width 0.1))
  (fp_line (start 0.2 -1.05) (end 0.2 1.05) (layer F.Fab) (width 0.12))
  (pad 1 smd rect (at -1.15 0) (size 1.15 1.25) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1.15 0) (size 1.15 1.25) (layers F.Cu F.Paste F.Mask))
)""")

    (PRETTY / "RP2040_Pico_Header.kicad_mod").write_text("""(module RP2040_Pico_Header (layer F.Cu) (tedit 0)
  (descr "Raspberry Pi Pico 2x20 header footprint, 2.54mm pitch")
  (tags "Raspberry Pi Pico RP2040 module") (attr through_hole)
  (fp_text reference REF** (at 0 -27.5) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value RP2040_Pico (at 0 27.5) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -10.5 -25.4) (end 10.5 25.4) (layer F.Fab) (width 0.15))
  (fp_rect (start -10.5 -28.2) (end 10.5 -23.5) (layer F.Fab) (width 0.15))
""" + "\n".join(
        f'  (pad {n} thru_hole circle (at {x} {y:.2f}) (size 1.8 1.8) (drill 1.0) (layers *.Cu *.Mask))'
        for i in range(20)
        for n, x, y in ((2 * i + 1, -8.89, -24.13 + 2.54 * i), (2 * i + 2, 8.89, -24.13 + 2.54 * i))
    ) + "\n)\n")

    (PRETTY / "R_0603.kicad_mod").write_text("""(module R_0603 (layer F.Cu) (tedit 0) (descr "0603 resistor") (tags "0603 resistor") (attr smd)
  (fp_text reference REF** (at 0 -1.4) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_text value R_0603 (at 0 1.4) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -0.8 -0.45) (end 0.8 0.45) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -0.8 0) (size 0.9 1) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 0.8 0) (size 0.9 1) (layers F.Cu F.Paste F.Mask))
)""")

    (PRETTY / "PTC_1206.kicad_mod").write_text("""(module PTC_1206 (layer F.Cu) (tedit 0) (descr "1206 resettable fuse") (tags "1206 PTC fuse") (attr smd)
  (fp_text reference REF** (at 0 -1.6) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_text value PTC_1206 (at 0 1.6) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.7 -0.9) (end 1.7 0.9) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -1.2 0) (size 1.1 1.4) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1.2 0) (size 1.1 1.4) (layers F.Cu F.Paste F.Mask))
)""")

    (PRETTY / "C_Radial_D8.kicad_mod").write_text("""(module C_Radial_D8 (layer F.Cu) (tedit 0) (descr "Radial electrolytic capacitor, 8mm body") (tags "radial capacitor") (attr through_hole)
  (fp_text reference REF** (at 0 -5) (layer F.SilkS) (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value C_Radial_D8 (at 0 5) (layer F.Fab) (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_circle (center 0 0) (end 4 0) (layer F.Fab) (width 0.12))
  (fp_line (start -4 0) (end 4 0) (layer F.Fab) (width 0.12))
  (pad 1 thru_hole circle (at -1.75 0) (size 1.8 1.8) (drill 0.8) (layers *.Cu *.Mask))
  (pad 2 thru_hole circle (at 1.75 0) (size 1.8 1.8) (drill 0.8) (layers *.Cu *.Mask))
)""")

    (PRETTY / "AHCT1G125_SOT23-5.kicad_mod").write_text("""(module AHCT1G125_SOT23-5 (layer F.Cu) (tedit 0) (descr "74AHCT1G125 single buffer SOT-23-5") (tags "SOT-23-5 buffer") (attr smd)
  (fp_text reference REF** (at 0 -2.4) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_text value AHCT1G125 (at 0 2.4) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.5 -1.1) (end 1.5 1.1) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -2.0 -0.65) (size 1.2 0.45) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at -2.0 0) (size 1.2 0.45) (layers F.Cu F.Paste F.Mask))
  (pad 3 smd rect (at -2.0 0.65) (size 1.2 0.45) (layers F.Cu F.Paste F.Mask))
  (pad 4 smd rect (at 2.0 0.65) (size 1.2 0.6) (layers F.Cu F.Paste F.Mask))
  (pad 5 smd rect (at 2.0 -0.65) (size 1.2 0.6) (layers F.Cu F.Paste F.Mask))
)""")


def add_net(board, names):
    out = {}
    for name in names:
        # KiCad's root-sheet netlist names are slash-prefixed (for example,
        # "/GND"). Use the same canonical name so schematic parity checks do
        # not report every assigned pad as a conflict.
        board_name = name if name.startswith("unconnected-") else f"/{name}"
        net = pcbnew.NETINFO_ITEM(board, board_name)
        board.Add(net)
        out[name] = net.GetNetCode()
    return out


def load_fp(name: str):
    fp = pcbnew.FootprintLoad(str(PRETTY), name)
    if fp is None:
        raise RuntimeError(f"Could not load footprint {name} from {PRETTY}")
    return fp


def assign_pad_nets(fp, pads):
    for pad in fp.Pads():
        net_name = pads.get(str(pad.GetNumber()))
        if net_name:
            pad.SetNetCode(NET_CODES[net_name])


NET_CODES = {}


def place_fp(board, name, ref, value, x, y, angle=0, layer=pcbnew.F_Cu, pads=None, back=False):
    fp = load_fp(name)
    fp.SetFPID(pcbnew.LIB_ID("Cleaver", name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientationDegrees(angle)
    if not back:
        fp.SetLayer(layer)
    fp.SetPath(pcbnew.KIID_PATH("/" + component_uuid(ref)))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.Reference().SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
    board.Add(fp)
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        # Keep mirrored component references on fabrication artwork rather
        # than crowding the back silkscreen beside the switch/diode pads.
        fp.Reference().SetLayer(pcbnew.B_Fab)
    if pads:
        assign_pad_nets(fp, pads)
    return fp


def add_line(board, x1, y1, x2, y2, layer, width=0.05):
    item = pcbnew.PCB_SHAPE(board)
    item.SetShape(pcbnew.SHAPE_T_SEGMENT)
    item.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    item.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    item.SetLayer(layer)
    item.SetWidth(pcbnew.FromMM(width))
    board.Add(item)


def add_rect(board, x, y, w, h, layer=pcbnew.Dwgs_User, width=0.05):
    add_line(board, x, y, x + w, y, layer, width)
    add_line(board, x + w, y, x + w, y + h, layer, width)
    add_line(board, x + w, y + h, x, y + h, layer, width)
    add_line(board, x, y + h, x, y, layer, width)


def generate_board(keys, led_order):
    global NET_CODES
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetCopperLayerCount(2)
    board.GetTitleBlock().SetTitle("Cleaver full-size keyboard")
    board.GetTitleBlock().SetDate("2026-11-07")
    board.GetTitleBlock().SetRevision("0.1 - placement prototype")

    net_names = ["GND", "USB_5V", "LED_5V", "RGB_DATA", "RGB_BUF"]
    net_names += [f"ROW{i:02d}" for i in range(13)]
    net_names += [f"COL{i:02d}" for i in range(11)]
    net_names += [f"KEY{i:03d}" for i in range(1, 118)]
    net_names += [f"RGB_CHAIN_{i:03d}" for i in range(118)]
    unused_pico_pins = {
        "RUN": 30, "GP28": 34, "ADC_VREF": 35,
        "3V3_EN": 37, "3V3_OUT": 38, "VSYS": 39,
    }
    net_names += [f"unconnected-(U1-{pin}-Pad{number})" for pin, number in unused_pico_pins.items()]
    unused_led_output = "unconnected-(LED117-DOUT-Pad2)"
    net_names.append(unused_led_output)
    NET_CODES = add_net(board, net_names)

    # Outer board perimeter is the plate envelope (the supplied vector plate is rectangular).
    width, height = 452.4375, 147.6375
    add_rect(board, 0, 0, width, height, pcbnew.Edge_Cuts, 0.05)

    # Reference-only plate geometry: square switch apertures and stabilizer slots.
    # These drawings are deliberately on Dwgs.User, not Edge.Cuts or copper.
    for k in keys:
        add_rect(board, k["x"] - 7, k["y"] - 7, 14, 14)
    for x, y, w, h in parse_dxf_slots():
        add_rect(board, x, y, w, h)

    # Matrix keys, hotswap sockets, per-switch diodes, and RGB pixels.
    for k in keys:
        row, col = k["matrix_row"], k["matrix_col"]
        place_fp(
            board, "Kailh_socket_MX", k["ref"], k["legend"], k["x"], k["y"],
            pads={"1": f"ROW{row:02d}", "2": k["key_net"]},
        )
        place_fp(
            board, "D_SOD-123", k["diode"], "1N4148W", k["x"], k["y"] - 8.0,
            layer=pcbnew.B_Cu, back=True,
            pads={"1": k["key_net"], "2": f"COL{col:02d}"},
        )

    for k in led_order:
        place_fp(
            board, "SK6812MINI-E", k["led_ref"], f"RGB {k['legend']}",
            k["x"], k["y"] + 6.5,
            pads={
                "1": "LED_5V",
                "2": unused_led_output if k["led_index"] == len(led_order) - 1 else k["rgb_out"],
                "3": "GND", "4": k["rgb_in"],
            },
        )

    # Pico is rotated into the empty gap between M8 and M9. USB access must be
    # provided by the eventual case; this footprint is the 2x20 soldered module.
    pico_pads = {}
    gpio_to_net = {}
    for i, pin in enumerate(ROW_PINS):
        gpio_to_net[pin] = f"ROW{i:02d}"
    for i, pin in enumerate(COL_PINS):
        gpio_to_net[pin] = f"COL{i:02d}"
    gpio_to_net[RGB_PIN] = "RGB_DATA"
    pico_pin_numbers = {
        "GP0": 1, "GP1": 2, "GP2": 4, "GP3": 5, "GP4": 6, "GP5": 7,
        "GP6": 9, "GP7": 10, "GP8": 11, "GP9": 12, "GP10": 14, "GP11": 15,
        "GP12": 16, "GP13": 17, "GP14": 19, "GP15": 20, "GP16": 21,
        "GP17": 22, "GP18": 24, "GP19": 25, "GP20": 26, "GP21": 27,
        "GP22": 29, "GP26": 31, "GP27": 32, "GP28": 34,
    }
    for gpio, net in gpio_to_net.items():
        pico_pads[str(pico_pin_numbers[gpio])] = net
    for pin_name, number in unused_pico_pins.items():
        pico_pads[str(number)] = f"unconnected-(U1-{pin_name}-Pad{number})"
    for pin in [3, 8, 13, 18, 23, 28, 33, 36]:
        pico_pads[str(pin)] = "GND"
    pico_pads["40"] = "USB_5V"
    place_fp(board, "RP2040_Pico_Header", "U1", "Raspberry Pi Pico / RP2040", 227.6, 137.0, 90, pads=pico_pads)

    # USB-only current-limited RGB power and 3.3V-to-5V data translation.
    place_fp(board, "PTC_1206", "F1", "PTC 0.5A hold", 185.0, 124.0, pads={"1": "USB_5V", "2": "LED_5V"})
    place_fp(board, "C_Radial_D8", "C1", "470uF 6.3V", 194.0, 124.0, pads={"1": "LED_5V", "2": "GND"})
    place_fp(board, "AHCT1G125_SOT23-5", "U2", "74AHCT1G125", 185.0, 136.0,
            pads={"1": "GND", "2": "RGB_DATA", "3": "GND", "4": "RGB_BUF", "5": "LED_5V"})
    place_fp(board, "R_0603", "R1", "330R", 193.0, 136.0, pads={"1": "RGB_BUF", "2": "RGB_CHAIN_000"})

    # Add a small alignment mark and explanatory board note, outside manufacturing layers.
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("CLEAVER - 117 MX / SK6812MINI-E - UNROUTED STARTER")
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(3), pcbnew.FromMM(4)))
    txt.SetLayer(pcbnew.Dwgs_User)
    txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
    txt.SetTextThickness(pcbnew.FromMM(0.15))
    board.Add(txt)

    OUT.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(OUT / f"{NAME}.kicad_pcb"), board)


def parse_dxf_slots():
    """Return centers/size of the 16 non-switch stabilizer openings in SVG coordinates."""
    path = INPUT / "plate-2026-11-07T22_24_25.197Z.dxf"
    lines = path.read_text().splitlines()
    pairs = list(zip(lines[::2], lines[1::2]))
    entities, cur = [], None
    for code, value in pairs:
        code = int(code)
        if code == 0:
            if cur:
                entities.append(cur)
            cur = {"type": value, "data": []}
        elif cur:
            cur["data"].append((code, value))
    if cur:
        entities.append(cur)
    entities = [e for e in entities if e["type"] in ("LINE", "ARC")]
    slots = []
    for i in range(0, len(entities) - 7, 8):
        block = entities[i : i + 8]
        ls = [e for e in block if e["type"] == "LINE"]
        if len(ls) != 4:
            continue
        data = [{int(c): float(v) for c, v in e["data"]} for e in ls]
        xs = [d[g] for d in data for g in (10, 11)]
        ys = [-d[g] for d in data for g in (20, 21)]
        w, h = round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)
        if (w, h) not in ((14.0, 14.0), (7.0, 15.0), (15.0, 7.0)):
            continue
        if (w, h) != (14.0, 14.0):
            slots.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, w, h))
    if len(slots) != 16:
        raise ValueError(f"Expected 16 plate stabilizer openings, found {len(slots)}")
    return slots


def sym_property(name, value, pid, x, y, hide=False, justify=""):
    h = " hide" if hide else ""
    j = f" (justify {justify})" if justify else ""
    return f'    (property {q(name)} {q(value)} (id {pid}) (at {x:.4f} {y:.4f} 0) (effects (font (size 1 1)){j}{h}))'


def pin_def(number, name, x, y, angle=0, electrical="passive", length=2.54):
    return (
        f'      (pin {electrical} line (at {x:.4f} {y:.4f} {angle}) (length {length:.4f}) '
        f'(name {q(name)} (effects (font (size 1 1)))) '
        f'(number {q(str(number))} (effects (font (size 1 1)))))'
    )


def library_symbol(name, ref, value, footprint, graphic, pins, qualified=False):
    lib_name = f"Cleaver:{name}" if qualified else name
    x0, y0 = 0, 0
    header = [
        f'  (symbol {q(lib_name)} (pin_names (offset 0.7) hide) (in_bom yes) (on_board yes)',
        sym_property("Reference", ref, 0, 0, 5),
        sym_property("Value", value, 1, 0, -5),
        sym_property("Footprint", footprint, 2, 0, 0, True),
        sym_property("Datasheet", "~", 3, 0, 0, True),
        f'    (symbol {q(name + "_0_1")}',
    ]
    header.extend(graphic)
    header.append("    )")
    header.append(f'    (symbol {q(name + "_1_1")}')
    header.extend(pins)
    header.extend(["    )", "  )"])
    return "\n".join(header)


def symbol_definitions(qualified=False):
    rect = lambda x1, y1, x2, y2: f'      (rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.15)) (fill (type background)))'
    line = lambda x1, y1, x2, y2: f'      (polyline (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0.15)) (fill (type none)))'
    out = []
    out.append(library_symbol("KeySwitch", "SW", "KeySwitch", "Cleaver:Kailh_socket_MX",
        [rect(-2.54, 2.54, 2.54, -2.54), line(-1.4, -0.8, 1.4, 0.8)],
        [pin_def(1, "ROW", -5.08, 0, 0), pin_def(2, "KEY", 5.08, 0, 180)], qualified))
    out.append(library_symbol("KeyDiode", "D", "1N4148W", "Cleaver:D_SOD-123",
        [rect(-2, 1.8, 2, -1.8), line(-0.5, 1.5, 1, 0), line(1, 0, -0.5, -1.5), line(-0.5, -1.5, -0.5, 1.5), line(0.8, 1.6, 0.8, -1.6)],
        [pin_def(1, "A", -5.08, 0, 0), pin_def(2, "K", 5.08, 0, 180)], qualified))
    out.append(library_symbol("SK6812", "LED", "SK6812MINI-E", "Cleaver:SK6812MINI-E",
        [rect(-2.54, 2.54, 2.54, -2.54), line(-1.1, 0, 1.1, 0)],
        [pin_def(1, "VDD", -5.08, 2.54, 0), pin_def(4, "DIN", -5.08, -2.54, 0),
         pin_def(2, "DOUT", 5.08, 2.54, 180), pin_def(3, "GND", 5.08, -2.54, 180)], qualified))
    out.append(library_symbol("PicoModule", "U", "Raspberry Pi Pico / RP2040", "Cleaver:RP2040_Pico_Header",
        [rect(-20.32, 26.67, 20.32, -26.67), line(-10, 0, 10, 0)], pico_pins(), qualified))
    out.append(library_symbol("AHCT1G125", "U", "74AHCT1G125", "Cleaver:AHCT1G125_SOT23-5",
        [rect(-5.08, 3.81, 5.08, -3.81)],
        [pin_def(1, "/OE", -7.62, 2.54, 0), pin_def(2, "A", -7.62, 0, 0),
         pin_def(3, "GND", -7.62, -2.54, 0), pin_def(4, "Y", 7.62, -2.54, 180),
         pin_def(5, "VCC", 7.62, 2.54, 180)], qualified))
    out.append(library_symbol("Fuse", "F", "PTC 0.5A hold", "Cleaver:PTC_1206",
        [rect(-2.54, 1.5, 2.54, -1.5), line(-1.4, 0, 1.4, 0)],
        [pin_def(1, "USB_5V", -5.08, 0, 0), pin_def(2, "LED_5V", 5.08, 0, 180)], qualified))
    out.append(library_symbol("Resistor", "R", "330R", "Cleaver:R_0603",
        [rect(-2.54, 1.4, 2.54, -1.4), line(-1.4, 0, 1.4, 0)],
        [pin_def(1, "A", -5.08, 0, 0), pin_def(2, "B", 5.08, 0, 180)], qualified))
    out.append(library_symbol("Capacitor", "C", "470uF 6.3V", "Cleaver:C_Radial_D8",
        [line(-1.2, 0.7, 1.2, 0.7), line(-1.2, -0.7, 1.2, -0.7)],
        [pin_def(1, "+", -5.08, 0, 0), pin_def(2, "-", 5.08, 0, 180)], qualified))
    return "\n".join(out)


def pico_pins():
    names = {
        1:"GP0", 2:"GP1", 3:"GND", 4:"GP2", 5:"GP3", 6:"GP4", 7:"GP5", 8:"GND",
        9:"GP6", 10:"GP7", 11:"GP8", 12:"GP9", 13:"GND", 14:"GP10", 15:"GP11", 16:"GP12",
        17:"GP13", 18:"GND", 19:"GP14", 20:"GP15", 21:"GP16", 22:"GP17", 23:"GND", 24:"GP18",
        25:"GP19", 26:"GP20", 27:"GP21", 28:"GND", 29:"GP22", 30:"RUN", 31:"GP26", 32:"GP27",
        33:"AGND", 34:"GP28", 35:"ADC_VREF", 36:"GND", 37:"3V3_EN", 38:"3V3_OUT", 39:"VSYS", 40:"VBUS",
    }
    pins = []
    for i in range(20):
        y = 24.13 - i * 2.54
        pins.append(pin_def(2 * i + 1, names[2 * i + 1], -25.4, y, 0, length=5.08))
        pins.append(pin_def(2 * i + 2, names[2 * i + 2], 25.4, y, 180, length=5.08))
    return pins


def schematic_label(name, x, y, side="right"):
    angle = 0 if side == "right" else 180
    justify = "left" if side == "right" else "right"
    return f'''  (label {q(name)} (at {x:.4f} {y:.4f} {angle})
    (effects (font (size 0.9 0.9)) (justify {justify} bottom))
    (uuid {uid()}))'''


def schematic_no_connect(x, y):
    return f'''  (no_connect (at {x:.4f} {y:.4f}) (uuid {uid()}))'''


def schematic_text(text, x, y, size=1.0):
    return f'''  (text {q(text)} (at {x:.4f} {y:.4f} 0)
    (effects (font (size {size} {size}))))'''


def schematic_component(lib_id, ref, value, footprint, x, y, pin_numbers):
    ident = component_uuid(ref)
    lines = [f'  (symbol (lib_id {q(lib_id)}) (at {x:.4f} {y:.4f} 0) (unit 1)',
             '    (in_bom yes) (on_board yes) (dnp no)', f'    (uuid {ident})',
             f'    (property "Reference" {q(ref)} (id 0) (at {x:.4f} {y-4.2:.4f} 0) (effects (font (size 0.9 0.9))))',
             f'    (property "Value" {q(value)} (id 1) (at {x:.4f} {y+4.2:.4f} 0) (effects (font (size 0.8 0.8))))',
             f'    (property "Footprint" {q(footprint)} (id 2) (at {x:.4f} {y:.4f} 0) (effects (font (size 1 1)) hide))',
             f'    (property "Datasheet" "~" (id 3) (at {x:.4f} {y:.4f} 0) (effects (font (size 1 1)) hide))']
    for pin in pin_numbers:
        lines.append(f'    (pin {q(str(pin))} (uuid {uid()}))')
    lines.append('  )')
    return ident, "\n".join(lines)


def generate_schematic(keys, led_order):
    library = symbol_definitions(qualified=True)
    symbols, labels, texts, instances, no_connects = [], [], [], [], []

    def add_component(lib, ref, value, fp, x, y, pins):
        ident, text = schematic_component(lib, ref, value, fp, x, y, pins)
        symbols.append(text)
        instances.append(f'''    (path "/{ident}" (reference {q(ref)}) (unit 1) (value {q(value)}) (footprint {q(fp)}))''')

    # Electrical switch/diode grid: matrix coordinates are intentionally explicit.
    for k in keys:
        row, col = k["matrix_row"], k["matrix_col"]
        x, y = 31.75 + col * 25.4, 41.91 + row * 25.4
        dx = x + 12.7
        add_component("Cleaver:KeySwitch", k["ref"], k["legend"], "Cleaver:Kailh_socket_MX", x, y, [1, 2])
        add_component("Cleaver:KeyDiode", k["diode"], "1N4148W", "Cleaver:D_SOD-123", dx, y, [1, 2])
        labels += [
            schematic_label(f"ROW{row:02d}", x - 5.08, y, "left"),
            schematic_label(k["key_net"], x + 5.08, y, "right"),
            schematic_label(k["key_net"], dx - 5.08, y, "left"),
            schematic_label(f"COL{col:02d}", dx + 5.08, y, "right"),
        ]
        texts.append(schematic_text(k["legend"][:16], x + 3, y + 7.4, 0.7))

    # One visible symbol per RGB pixel, chained in the same order as the PCB netlist.
    led_grid_cols = 9
    for i, k in enumerate(led_order):
        row, col = divmod(i, led_grid_cols)
        x, y = 406.4 + col * 25.4, 43.18 + row * 22.86
        add_component("Cleaver:SK6812", k["led_ref"], f"RGB {k['legend']}", "Cleaver:SK6812MINI-E", x, y, [1, 2, 3, 4])
        labels.extend([
            schematic_label("LED_5V", x - 5.08, y - 2.54, "left"),
            schematic_label(k["rgb_in"], x - 5.08, y + 2.54, "left"),
            schematic_label("GND", x + 5.08, y + 2.54, "right"),
        ])
        if i < len(led_order) - 1:
            labels.append(schematic_label(k["rgb_out"], x + 5.08, y - 2.54, "right"))
        else:
            no_connects.append(schematic_no_connect(x + 5.08, y - 2.54))

    # Pico symbol is the physical 2x20 module header pinout, not a bare RP2040 IC.
    px, py = 704.85, 198.12
    pico_names = {
        1:"GP0", 2:"GP1", 3:"GND", 4:"GP2", 5:"GP3", 6:"GP4", 7:"GP5", 8:"GND",
        9:"GP6", 10:"GP7", 11:"GP8", 12:"GP9", 13:"GND", 14:"GP10", 15:"GP11", 16:"GP12",
        17:"GP13", 18:"GND", 19:"GP14", 20:"GP15", 21:"GP16", 22:"GP17", 23:"GND", 24:"GP18",
        25:"GP19", 26:"GP20", 27:"GP21", 28:"GND", 29:"GP22", 30:"RUN", 31:"GP26", 32:"GP27",
        33:"AGND", 34:"GP28", 35:"ADC_VREF", 36:"GND", 37:"3V3_EN", 38:"3V3_OUT", 39:"VSYS", 40:"VBUS",
    }
    add_component("Cleaver:PicoModule", "U1", "Raspberry Pi Pico / RP2040", "Cleaver:RP2040_Pico_Header", px, py, range(1, 41))
    gpio_nets = {pin: f"ROW{i:02d}" for i, pin in enumerate(ROW_PINS)}
    gpio_nets.update({pin: f"COL{i:02d}" for i, pin in enumerate(COL_PINS)})
    gpio_nets[RGB_PIN] = "RGB_DATA"
    for pin_number, pin_name in pico_names.items():
        iy = 24.13 - ((pin_number - 1) // 2) * 2.54
        if pin_number % 2:
            lx, ly, side = px - 25.4, py - iy, "left"
        else:
            lx, ly, side = px + 25.4, py - iy, "right"
        if pin_name in gpio_nets:
            labels.append(schematic_label(gpio_nets[pin_name], lx, ly, side))
        elif pin_name in ("GND", "AGND"):
            labels.append(schematic_label("GND", lx, ly, side))
        elif pin_name == "VBUS":
            labels.append(schematic_label("USB_5V", lx, ly, side))
        elif pin_name in ("RUN", "GP28", "ADC_VREF", "3V3_EN", "3V3_OUT", "VSYS"):
            no_connects.append(schematic_no_connect(lx, ly))

    # Power protection, bulk capacitor, and 5V logic-level buffer for the RGB chain.
    fuse_y = 74.93
    add_component("Cleaver:Fuse", "F1", "PTC 0.5A hold", "Cleaver:PTC_1206", 635, fuse_y, [1, 2])
    labels.extend([schematic_label("USB_5V", 629.92, fuse_y, "left"), schematic_label("LED_5V", 640.08, fuse_y, "right")])
    cap_y = 99.06
    add_component("Cleaver:Capacitor", "C1", "470uF 6.3V", "Cleaver:C_Radial_D8", 635, cap_y, [1, 2])
    labels.extend([schematic_label("LED_5V", 629.92, cap_y, "left"), schematic_label("GND", 640.08, cap_y, "right")])
    u2_y = 144.78
    add_component("Cleaver:AHCT1G125", "U2", "74AHCT1G125", "Cleaver:AHCT1G125_SOT23-5", 635, u2_y, [1, 2, 3, 4, 5])
    labels.extend([
        schematic_label("GND", 627.38, u2_y - 2.54, "left"), schematic_label("RGB_DATA", 627.38, u2_y, "left"),
        schematic_label("GND", 627.38, u2_y + 2.54, "left"), schematic_label("RGB_BUF", 642.62, u2_y + 2.54, "right"),
        schematic_label("LED_5V", 642.62, u2_y - 2.54, "right"),
    ])
    resistor_y = 170.18
    add_component("Cleaver:Resistor", "R1", "330R", "Cleaver:R_0603", 635, resistor_y, [1, 2])
    labels.extend([schematic_label("RGB_BUF", 629.92, resistor_y, "left"), schematic_label("RGB_CHAIN_000", 640.08, resistor_y, "right")])

    header = f'''(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid {uid()})
  (paper "A1")
  (title_block (title "Cleaver full-size keyboard") (date "2026-11-07") (rev "0.1 - placement prototype"))
  (lib_symbols
{library}
  )
'''
    body = [
        schematic_text("CLEAVER - 117 MX HOT-SWAP KEYS / 13 x 11 MATRIX", 35, 20, 2.0),
        schematic_text("Diodes: ROW2COL. U1 is a Raspberry Pi Pico module; USB data/power uses Pico's onboard micro-USB connector.", 35, 26, 1.0),
        schematic_text("RGB: 117 x SK6812MINI-E, serpentine order. USB-only: 500mA PTC and initial QMK brightness cap 12/255.", 35, 31, 1.0),
        schematic_text("Plate overlay geometry is from the supplied DXF; board remains unrouted and needs mechanical/case review.", 35, 36, 1.0),
    ] + texts + labels + no_connects + symbols
    header += "\n".join(body)
    header += f'''\n  (sheet_instances (path "/" (page "1")))
  (symbol_instances
{chr(10).join(instances)}
  )
  (embedded_fonts no)
)\n'''
    (OUT / f"{NAME}.kicad_sch").write_text(header)


def generate_tables_and_project():
    (OUT / "fp-lib-table").write_text('''(fp_lib_table
  (lib (name "Cleaver") (type "KiCad") (uri "${KIPRJMOD}/Cleaver.pretty") (options "") (descr "Project-local Cleaver keyboard footprints"))
)\n''')
    (OUT / "sym-lib-table").write_text('''(sym_lib_table
  (lib (name "Cleaver") (type "KiCad") (uri "${KIPRJMOD}/Cleaver.kicad_sym") (options "") (descr "Project-local Cleaver keyboard symbols"))
)\n''')
    (OUT / "Cleaver.kicad_sym").write_text(
        '(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n' +
        symbol_definitions(qualified=False) + '\n)\n'
    )
    (OUT / "Cleaver.kicad_pro").write_text('{}\n')


def generate_firmware_files(keys, led_order):
    fw = OUT / "firmware"
    fw.mkdir(parents=True, exist_ok=True)
    qmk = {
        "keyboard_name": "Cleaver",
        "manufacturer": "Cleaver keyboard project",
        "maintainer": "cleaver",
        "processor": "RP2040",
        "bootloader": "rp2040",
        "matrix_pins": {"rows": ROW_PINS, "cols": COL_PINS},
        "diode_direction": "ROW2COL",
        "usb": {"vid": "0xFEED", "pid": "0xC1EA", "device_version": "0.1.0"},
        "rgb_matrix": {
            "driver": "ws2812",
            "max_brightness": 12,
            "layout": [
                {
                    "matrix": [k["matrix_row"], k["matrix_col"]],
                    "x": round(k["x"] / 452.4375 * 224, 2),
                    "y": round(k["y"] / 147.6375 * 64, 2),
                    "flags": 1,
                }
                for k in led_order
            ],
        },
    }
    (fw / "keyboard.json").write_text(json.dumps(qmk, indent=2) + "\n")
    (fw / "config.h").write_text("""#pragma once

#define MATRIX_ROWS 13
#define MATRIX_COLS 11
#define MATRIX_ROW_PINS { GP0, GP1, GP2, GP3, GP4, GP5, GP6, GP7, GP8, GP9, GP10, GP11, GP12 }
#define MATRIX_COL_PINS { GP13, GP14, GP15, GP16, GP17, GP18, GP19, GP20, GP21, GP22, GP26 }
#define DIODE_DIRECTION ROW2COL

#define WS2812_DI_PIN GP27
#define RGB_MATRIX_LED_COUNT 117
// Conservative USB-only starting point; increase only after measuring total current.
#define RGB_MATRIX_MAXIMUM_BRIGHTNESS 12
#define USB_MAX_POWER_CONSUMPTION 500
""")
    (fw / "rules.mk").write_text("""BOARD = GENERIC_RP_RP2040
BOOTLOADER = rp2040
RGB_MATRIX_ENABLE = yes
RGB_MATRIX_DRIVER = WS2812
WS2812_DRIVER = vendor
""")
    with (fw / "key_matrix.csv").open("w") as f:
        f.write("ref,legend,matrix_row,matrix_col,plate_x_mm,plate_y_mm,rgb_chain_index\n")
        for k in keys:
            f.write(f'{k["ref"]},{q(k["legend"])[1:-1]},{k["matrix_row"]},{k["matrix_col"]},{k["x"]:.4f},{k["y"]:.4f},{k["led_index"]}\n')


def write_readme(keys):
    (OUT / "README.md").write_text("""# Cleaver KiCad starter project

This project is generated from the supplied KLE JSON and plate DXF. It contains **117 MX switch positions**, one Kailh MX hotswap socket footprint and one 1N4148W diode per key, and **117 SK6812MINI-E addressable RGB pixels**. The three lock-indicator graphics in the KLE are decals, not switch/LED footprints.

## Controller and matrix

The proposed controller is a soldered Raspberry Pi Pico (RP2040) module on a 2x20, 2.54 mm header footprint. QMK supports RP2040; Vial-QMK lists RP2040 as a compatible MCU. The board uses a **13 x 11** diode matrix plus one RGB data pin, which consumes 25 of the Pico's 26 exposed GPIOs.

| Signal | Pico GPIOs |
|---|---|
| Matrix rows R00–R12 | GP0–GP12 |
| Matrix columns C00–C10 | GP13–GP22, GP26 |
| RGB data | GP27 |
| Spare | GP28 |

`firmware/key_matrix.csv` is the generated physical-key to electrical-matrix map. `firmware/config.h`, `rules.mk`, and `keyboard.json` are starting points to copy into a Vial-QMK keyboard definition, not a complete Vial keyboard directory/keymap.

## RGB and USB power limitation

The RGB chain is SK6812MINI-E (not SK6812MINI; verify the exact suffix and pinout when purchasing). The 74AHCT1G125 translates the Pico's 3.3 V data to a solid 5 V LED data level; R1 is a 330 ohm data resistor. F1 is a resettable fuse specified as 0.5 A hold, and C1 is a 470 uF bulk capacitor.

Full-white current for 117 pixels is far beyond USB capability. The supplied QMK starting configuration caps `RGB_MATRIX_MAXIMUM_BRIGHTNESS` at **12/255** and declares 500 mA USB maximum. This is only a conservative initial estimate: LED vendor current varies, so measure current on the assembled board and lower the cap if needed. Do not raise it or enable full-white until power is upgraded. The Pico's onboard USB connector supplies both controller and LED power through VBUS.

## Important status

The PCB file is a **placement and net-assignment starter, not a finished manufacturing design**. It has no copper routing, ground plane, USB connector footprint (the Pico's own connector is used), case, mounting holes, or verified fabrication clearances. The Pico sits in the open gap between M8 and M9; make a case opening/cable path for its USB port. The top-side RGB LED position is a first-pass placement and must be checked against the specific switch housing/LED window and case stack-up. Verify the 14 mm plate cutouts and stabilizer clearance against the DXF before fabrication.

The key apertures and 16 plate stabilizer slots are shown on `Dwgs.User` for reference only; the board edge follows the plate's 452.438 x 147.638 mm envelope. Keep `Dwgs.User` out of fabrication Gerbers.

## Validation snapshot

Checked with KiCad CLI 10.0.8: schematic ERC reports **0 errors and 0 warnings**; PCB DRC with schematic parity reports **0 violations and 0 parity errors**. DRC still reports **499 unconnected pads** because no copper has been routed; this is expected for this placement prototype and must be resolved by routing before fabrication.

Before ordering: complete routing, add mounting features/connector access, confirm the chosen SK6812MINI-E and switch/socket datasheets, run ERC/DRC, and inspect the board against a 1:1 plate print.

## Regeneration

From the repository root, run `python scripts/generate_kicad.py`. It reads the layout JSON and DXF under `plate-2026-11-07T22_24_25.197Z/` and writes the KiCad files under `kicad/`.
""")


def main():
    keys, led_order = read_keys()
    write_custom_footprints()
    generate_tables_and_project()
    generate_board(keys, led_order)
    generate_schematic(keys, led_order)
    generate_firmware_files(keys, led_order)
    write_readme(keys)
    print(f"Generated KiCad project with {len(keys)} keys, 13x11 matrix and {len(led_order)} RGB LEDs")


if __name__ == "__main__":
    main()
