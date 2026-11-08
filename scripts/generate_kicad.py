#!/usr/bin/env python3
"""Build Cleaver revision 0.3; import a Specctra session for the routed PCB.

The electrical model is in design.py. No geometry-only wiring guesses are made:
the PCB takes its pad nets from KiCad's exported schematic netlist. Project rules
are preserved except for adding the explicit low-current power net class.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from design import (ROOT, INPUT, U, BOARD_W, BOARD_H, ROW_GPIOS, COL_GPIOS,
                    MODULE_PINS, RGB_GPIO, POWER_GPIO, read_keys, components,
                    default_keycodes)
from models_3d import update_library_models

OUT = ROOT / "kicad"
PRETTY = OUT / "Cleaver.pretty"
ROOT_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "cleaver:schematic:0.3"))
FP_NAMES = {"MX": "Kailh_socket_MX"}


def ident(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "cleaver:0.3:" + name))


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def pin(n, name, typ, x, y, angle=0):
    return (str(n), name, typ, x, y, angle)


def symbol_pins():
    module = []
    for n, name in MODULE_PINS.items():
        typ = ("power_in" if name in ("GND", "VIN") else "power_out"
               if name in ("3V3_OUT", "VOUT") else "input" if name == "RUN" else "bidirectional")
        left = n <= 20
        level = n - 1 if left else 40 - n
        module.append(pin(n, name, typ, -25.4 if left else 25.4,
                          24.13 - 2.54 * level, 0 if left else 180))
    two = [pin(1, "1", "passive", -5.08, 0), pin(2, "2", "passive", 5.08, 0, 180)]
    return {
        "YD_RP2040": module,
        "MX": [pin(1, "ROW", "passive", -5.08, 0), pin(2, "KEY", "passive", 5.08, 0, 180)],
        "D_SOD123": [pin(2, "A", "passive", -5.08, 0), pin(1, "K", "passive", 5.08, 0, 180)],
        "MINI_E": [pin(1, "VDD", "power_in", -5.08, 2.54),
                   pin(4, "DIN", "input", -5.08, -2.54),
                   pin(2, "DOUT", "output", 5.08, 2.54, 180),
                   pin(3, "GND", "power_in", 5.08, -2.54, 180)],
        "LV1T125": [pin(1, "~{OE}", "input", -7.62, 2.54),
                     pin(2, "A", "input", -7.62, 0),
                     pin(3, "GND", "power_in", -7.62, -2.54),
                     pin(4, "Y", "tri_state", 7.62, -2.54, 180),
                     pin(5, "VCC", "power_in", 7.62, 2.54, 180)],
        "TPS2553": [pin(1, "IN", "power_in", -7.62, 5.08),
                      pin(2, "GND", "power_in", -7.62, -5.08),
                      pin(3, "EN", "input", -7.62, 0),
                      pin(4, "~{FAULT}", "open_collector", 7.62, -5.08, 180),
                      pin(5, "ILIM", "passive", 7.62, 0, 180),
                      pin(6, "OUT", "power_out", 7.62, 5.08, 180)],
        "WirePad": [pin(1, "VBUS", "passive", 5.08, 0, 180)],
        "R_0805": two, "C_0805": two, "PTC_1206": two,
        "C_Radial8": [pin(1, "+", "passive", -5.08, 0), pin(2, "-", "passive", 5.08, 0, 180)],
        "PowerFlag": [pin(1, "pwr", "power_out", 0, 0)],
    }


PINS = symbol_pins()


def footprint(kind, pads, body, extra="", through=False):
    name = FP_NAMES.get(kind, kind)
    x, y = body
    text = f'''(module {name} (layer F.Cu) (tedit 0)
  (descr {q('Cleaver verified geometry: ' + kind)})
  (attr {'through_hole' if through else 'smd'})
  (fp_text reference REF** (at 0 {-y - 1.2}) (layer F.SilkS)
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value {name} (at 0 {y + 1.2}) (layer F.Fab)
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_rect (start {-x} {-y}) (end {x} {y}) (layer F.Fab) (width 0.1))
  {pads}
  {extra}
)'''
    return "\n".join(line.rstrip() for line in text.splitlines())


def smd(n, x, y, w, h):
    return f'(pad {n} smd rect (at {x} {y}) (size {w} {h}) (layers F.Cu F.Paste F.Mask))'


def write_footprints():
    PRETTY.mkdir(exist_ok=True)
    if not (PRETTY / "Kailh_socket_MX.kicad_mod").exists():
        raise FileNotFoundError("The vendored, licensed Kailh MX socket footprint is required")
    definitions = {}
    for kind in ("R_0805", "C_0805"):
        definitions[kind] = footprint(kind, smd(1, -.95, 0, 1.1, 1.4) + smd(2, .95, 0, 1.1, 1.4), (1, .625))
    definitions["D_SOD123"] = footprint("D_SOD123",
        smd(1, -1.65, 0, .9, 1.2) + smd(2, 1.65, 0, .9, 1.2), (1.4, .9),
        '(fp_line (start -2.45 -0.8) (end -2.45 0.8) (layer F.SilkS) (width 0.15))')
    definitions["PTC_1206"] = footprint("PTC_1206",
        smd(1, -1.45, 0, 1.4, 1.8) + smd(2, 1.45, 0, 1.4, 1.8), (1.6, .8))
    # DBV SOT-23 lead pitch is 0.95 mm. TI's LV1T125 uses 3+2 leads;
    # TPS2553 uses all six leads, with the same package outline.
    for kind, numbers in (("LV1T125", [(1,-1,-1),(2,-1,0),(3,-1,1),(4,1,1),(5,1,-1)]),
                          ("TPS2553", [(1,-1,-1),(2,-1,0),(3,-1,1),(4,1,1),(5,1,0),(6,1,-1)])):
        definitions[kind] = footprint(kind,
            "\n".join(smd(n, x * 1.1375, y * .95, 1.325, .6) for n,x,y in numbers), (.8, 1.45))
    # Rev02 function numbering, viewed from the component's solder side, with
    # its emitter pointing THROUGH the board (reverse mount). Mirror the
    # emitter-view datasheet once here, before KiCad's normal B.Cu flip.
    # 3.6 x 3.2 opening accommodates the 3.2 x 2.8 body; >=0.5 mm copper
    # clearance is retained even with Edge.Cuts line width included.
    definitions["MINI_E"] = footprint("MINI_E", "\n".join([
        smd(1, -3.05, .75, 1.4, .9), smd(2, -3.05, -.75, 1.4, .9),
        smd(3, 3.05, -.75, 1.4, .9), smd(4, 3.05, .75, 1.4, .9)]), (1.6, 1.4), '''
        (fp_rect (start -1.8 -1.6) (end 1.8 1.6) (layer Edge.Cuts) (width 0.05))
        (fp_line (start 3.3 -1.6) (end 3.8 -1.6) (layer F.SilkS) (width 0.12))
        (fp_line (start 3.8 -1.6) (end 3.8 -1.35) (layer F.SilkS) (width 0.12))''')
    pads = []
    for i in range(20):
        for n,x in ((i+1,-8.89),(40-i,8.89)):
            pads.append(f'(pad {n} thru_hole {"rect" if n == 1 else "circle"} '
                        f'(at {x} {-24.13+2.54*i:.2f}) (size 1.8 1.8) (drill 1) (layers *.Cu *.Mask))')
    definitions["YD_RP2040"] = footprint("YD_RP2040", "\n".join(pads), (11.43, 26.67), '''
        (fp_rect (start -4.5 -27) (end 4.5 -19) (layer F.Fab) (width 0.1))
        (fp_text user "USB-C -> EDGE" (at 0 -17) (layer F.SilkS)
          (effects (font (size 1 1) (thickness 0.15))))''', through=True)
    definitions["WirePad"] = footprint("WirePad",
        '(pad 1 thru_hole circle (at 0 0) (size 2.4 2.4) (drill 1.0) (layers *.Cu *.Mask))',
        (1.2, 1.2), through=True)
    definitions["C_Radial8"] = footprint("C_Radial8", '''
        (pad 1 thru_hole rect (at -1.75 0) (size 1.8 1.8) (drill 0.8) (layers *.Cu *.Mask))
        (pad 2 thru_hole circle (at 1.75 0) (size 1.8 1.8) (drill 0.8) (layers *.Cu *.Mask))''',
        (4,4), '''
        (fp_circle (center 0 0) (end 4 0) (layer F.SilkS) (width 0.12))
        (fp_text user "+" (at -4.8 0) (layer F.SilkS)
          (effects (font (size 1 1) (thickness 0.15))))''', through=True)
    for kind, text in definitions.items():
        (PRETTY / f"{kind}.kicad_mod").write_text(text + "\n")
    update_library_models(PRETTY)


def symbol_definition(kind, qualified):
    name = f"Cleaver:{kind}" if qualified else kind
    width, height = ((20.32, 26.67) if kind == "YD_RP2040" else
                     (5.08, 6.35) if kind == "TPS2553" else
                     (5.08, 3.81) if kind == "LV1T125" else (2.54, 3.81))
    p = []
    for n, label, typ, x, y, angle in PINS[kind]:
        length = 0 if kind == 'PowerFlag' else 5.08 if kind == 'YD_RP2040' else 2.54
        p.append(f'''(pin {typ} line (at {x} {y} {angle}) (length {length})
          (name {q(label)} (effects (font (size 0.8 0.8))))
          (number {q(n)} (effects (font (size 0.8 0.8)))))''')
    graphic = f'(rectangle (start {-width} {height}) (end {width} {-height}) (stroke (width 0.15)) (fill (type background)))'
    if kind == "D_SOD123":
        graphic = '''(polyline (pts (xy -1.5 1.5) (xy -1.5 -1.5) (xy 1.5 0) (xy -1.5 1.5)) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy 1.5 1.5) (xy 1.5 -1.5)) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy -1.5 0)) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy 1.5 0) (xy 2.54 0)) (stroke (width 0.15)) (fill (type none)))'''
    elif kind in ("C_0805", "C_Radial8"):
        graphic = '''(polyline (pts (xy -0.6 2) (xy -0.6 -2)) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy 0.6 2) (xy 0.6 -2)) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy -0.6 0)) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy 0.6 0) (xy 2.54 0)) (stroke (width 0.15)) (fill (type none)))'''
    elif kind == "PowerFlag":
        graphic = '(polyline (pts (xy 0 0) (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 0)) (stroke (width 0.15)) (fill (type none)))'
    elif kind == "MX":
        graphic = '''(circle (center -2.54 0) (radius 0.4) (stroke (width 0.15)) (fill (type none)))
        (circle (center 2.54 0) (radius 0.4) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy 2.54 1.27)) (stroke (width 0.15)) (fill (type none)))'''
    elif kind in ("R_0805", "PTC_1206"):
        graphic = '(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width 0.15)) (fill (type none)))'
    elif kind == "WirePad":
        graphic = '''(circle (center 0 0) (radius 1.27) (stroke (width 0.15)) (fill (type none)))
        (polyline (pts (xy 1.27 0) (xy 2.54 0)) (stroke (width 0.15)) (fill (type none)))'''
    fp = "" if kind == "PowerFlag" else f"Cleaver:{FP_NAMES.get(kind, kind)}"
    hide = '' if kind in ('YD_RP2040','MINI_E','TPS2553','LV1T125','C_Radial8') else ' hide'
    return f'''(symbol {q(name)} (pin_names (offset 0.7){hide}) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 5 0) (effects (font (size 1 1))))
      (property "Value" {q(kind)} (at 0 -5 0) (effects (font (size 1 1))))
      (property "Footprint" {q(fp)} (at 0 0 0) (effects (font (size 1 1)) hide))
      (symbol {q(kind + '_0_1')} {graphic})
      (symbol {q(kind + '_1_1')} {' '.join(p)}))'''


def generate_schematic(parts, keys, leds):
    body, instances = [], []
    positions = {}
    wired_pins = {('TP1','1'),('F1','1'),('F1','2'),('U3','1'),('U2','4'),('R1','1')}
    key_index = {k["ref"]: i for i,k in enumerate(keys)}
    led_index = {k["led_ref"]: i for i,k in enumerate(leds)}
    cap_index = {k["cap_ref"]: i for i,k in enumerate(leds)}
    corner_index = 0
    all_parts = parts + [dict(ref="#FLG01", kind="PowerFlag", value="PWR_FLAG", pins={"1":"GND"}),
                         dict(ref="#FLG02", kind="PowerFlag", value="PWR_FLAG", pins={"1":"FUSED_5V"}),
                         dict(ref="#FLG03", kind="PowerFlag", value="PWR_FLAG", pins={"1":"RAW_USB_5V"})]
    for part in all_parts:
        ref, kind = part["ref"], part["kind"]
        if ref.startswith("SW") or (ref.startswith("D") and ref[1:].isdigit()):
            index = key_index[ref if ref.startswith("SW") else "SW" + ref[1:]]
            row, col = divmod(index, 16)
            x, y = 30 + col * 35.56 + (15.24 if kind == "D_SOD123" else 0), 55 + row * 30.48
        elif ref in led_index or ref in cap_index:
            index = led_index[ref] if ref in led_index else cap_index[ref]
            row, col = divmod(index, 8)
            x, y = 645 + col * 60.96 + (27.94 if ref in cap_index else 0), 55 + row * 30.48
        elif ref == "U1":
            x,y = 65, 430
        else:
            x,y = 150 + (corner_index % 6) * 66.04, 360 + (corner_index // 6) * 45.72
            corner_index += 1
        # All symbol pins and labels must land on KiCad's 50 mil connection grid.
        x, y = round(x / 1.27) * 1.27, round(y / 1.27) * 1.27
        positions[ref] = (x,y)
        cid = ident(ref)
        fp = "" if kind == "PowerFlag" else f"Cleaver:{FP_NAMES.get(kind,kind)}"
        on_board = "no" if kind == "PowerFlag" else "yes"
        ref_y = y - (29.21 if kind == 'YD_RP2040' else 8.89 if kind in ('TPS2553','LV1T125') else 5.08)
        value_y = y + (29.21 if kind == 'YD_RP2040' else 8.89 if kind in ('TPS2553','LV1T125') else 6.35)
        body.append(f'''(symbol (lib_id "Cleaver:{kind}") (at {x:.4f} {y:.4f} 0) (unit 1)
          (in_bom {on_board}) (on_board {on_board}) (dnp no) (uuid {cid})
          (property "Reference" {q(ref)} (at {x:.4f} {ref_y:.4f} 0) (effects (font (size 0.8 0.8))))
          (property "Value" {q(part['value'])} (at {x:.4f} {value_y:.4f} 0) (effects (font (size 0.7 0.7))))
          (property "Footprint" {q(fp)} (at {x:.4f} {y:.4f} 0) (effects (font (size 1 1)) hide))
          {' '.join(f'(pin {q(p[0])} (uuid {ident(ref + ":pin:" + p[0])}))' for p in PINS[kind])})''')
        instances.append(f'(path "/{cid}" (reference {q(ref)}) (unit 1) (value {q(part["value"])}) (footprint {q(fp)}))')
        for n, name, typ, px, py, angle in PINS[kind]:
            lx, ly = x + px, y - py
            net = part["pins"].get(n)
            if (kind in ('MX','D_SOD123') and n=='2') or (ref,n) in wired_pins:
                continue
            if net is None:
                body.append(f'(no_connect (at {lx:.4f} {ly:.4f}) (uuid {ident(ref+":nc:"+n)}))')
            else:
                body.append(f'''(label {q(net)} (at {lx:.4f} {ly:.4f} {180 if px < 0 else 0})
                  (effects (font (size 0.7 0.7)) (justify {'right' if px < 0 else 'left'} bottom))
                  (uuid {ident(ref+":net:"+n)}))''')
    def wire(net, points, name):
        for index,(a,b) in enumerate(zip(points,points[1:])):
            body.append(f'''(wire (pts (xy {a[0]:.4f} {a[1]:.4f}) (xy {b[0]:.4f} {b[1]:.4f}))
              (stroke (width 0) (type default)) (uuid {ident(name+':wire:'+str(index))}))''')
        x,y = points[0]
        body.append(f'''(label {q(net)} (at {x:.4f} {y:.4f} 0)
          (effects (font (size 0.7 0.7)) (justify left bottom)) (uuid {ident(name+':wire-label')}))''')
    for key in keys:
        x,y = positions[key['ref']]
        wire(key['key_net'], [(x+5.08,y),(x+10.16,y)], key['ref'])
    x,y = positions['TP1']; fx,fy = positions['F1']; ux,uy = positions['U3']
    wire('RAW_USB_5V',[(x+5.08,y),(fx-5.08,fy)],'USB-input')
    wire('FUSED_5V',[(fx+5.08,fy),(ux-20.32,fy),(ux-20.32,uy-5.08),(ux-7.62,uy-5.08)],'protected-input')
    x,y = positions['U2']; rx,ry = positions['R1']
    wire('RGB_BUFFERED',[(x+7.62,y+2.54),(rx-7.62,y+2.54),(rx-7.62,ry),(rx-5.08,ry)],'RGB-buffer')
    header = f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0")
      (uuid {ROOT_ID}) (paper "A0")
      (title_block (title "Cleaver - YD-RP2040 USB-C") (date "2026-11-08") (rev "0.3"))
      (lib_symbols {' '.join(symbol_definition(k, True) for k in PINS)})
      (text "117 UNIQUE KEYS - 8x16 ROW2COL - USB POWER ONLY - NO POWER SWITCH" (at 30 20 0)
        (effects (font (size 2 2)) (justify left)))
      (text "YD-RP2040 pin40 UNUSED. TP1: raw USB VBUS tap BEFORE diode. RGB enable GP28; data GP27; brightness 8/255." (at 30 30 0)
        (effects (font (size 1.2 1.2)) (justify left)))
      {' '.join(body)}
      (sheet_instances (path "/" (page "1"))) (symbol_instances {' '.join(instances)})
      (embedded_fonts no))\n'''
    (OUT / "Cleaver.kicad_sch").write_text(header)
    (OUT / "Cleaver.kicad_sym").write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n' +
        "\n".join(symbol_definition(k, False) for k in PINS) + ')\n')
    (OUT / "fp-lib-table").write_text('(fp_lib_table (lib (name "Cleaver") (type "KiCad") (uri "${KIPRJMOD}/Cleaver.pretty") (options "") (descr "Cleaver local footprints")))\n')
    (OUT / "sym-lib-table").write_text('(sym_lib_table (lib (name "Cleaver") (type "KiCad") (uri "${KIPRJMOD}/Cleaver.kicad_sym") (options "") (descr "Cleaver local symbols")))\n')


def schematic_nets(report_dir):
    dest = report_dir / "netlist.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(dest), str(OUT / "Cleaver.kicad_sch")], check=True)
    root = ET.parse(dest).getroot()
    return {(p.get("ref"), p.get("pin")): n.get("name")
            for n in root.findall("./nets/net") for p in n.findall("node")}


def update_netclasses():
    path = OUT / "Cleaver.kicad_pro"
    project = json.loads(path.read_text())
    settings = project["net_settings"]
    settings["netclass_patterns"] = [item for item in settings["netclass_patterns"]
                                     if item != {"netclass":"USB_LED_Power", "pattern":"/MODULE_VOUT"}]
    classes = settings["classes"]
    next(c for c in classes if c["name"] == "Default")["track_width"] = .3
    if not any(c["name"] == "USB_LED_Power" for c in classes):
        default = next(c for c in classes if c["name"] == "Default")
        classes.append(dict(default, name="USB_LED_Power", priority=0, track_width=.6,
                            via_diameter=.8, via_drill=.4, clearance=.2))
    for net in ("RAW_USB_5V", "FUSED_5V", "LED_5V", "GND"):
        item = {"netclass": "USB_LED_Power", "pattern": "/" + net}
        if item not in settings["netclass_patterns"]:
            settings["netclass_patterns"].append(item)
    path.write_text(json.dumps(project, indent=2) + "\n")


def line(board, a, b, layer):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetStart(mm(*a)); shape.SetEnd(mm(*b))
    shape.SetLayer(layer); shape.SetWidth(pcbnew.FromMM(.05))
    board.Add(shape)


def ground_fanout(board, keys, parts, net):
    """Explicit solder-pad-free returns to the reserved inner ground plane.

    A DSN plane is not itself a connection to a bottom SMD pad. Pre-wire both
    grounds in each cell to a through-via; don't depend on router plane heuristics.
    """
    for k in keys:
        x, y = k["x"], k["y"] + 5.08
        points = [(x+3.05,y+.75), (x+4.05,y+1.75), (x+6.75,y+1.75), (x+6.75,y)]
        for a,b in zip(points,points[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(mm(*a)); t.SetEnd(mm(*b)); t.SetLayer(pcbnew.B_Cu)
            t.SetWidth(pcbnew.FromMM(.3)); t.SetNet(net); t.SetLocked(True)
            board.Add(t)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(mm(x+6.75,y+1.75)); v.SetWidth(pcbnew.FromMM(.7))
        v.SetDrill(pcbnew.FromMM(.3)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net); v.SetLocked(True); board.Add(v)
    kinds = {p["ref"]: p["kind"] for p in parts}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if kinds[ref] not in ("LV1T125", "TPS2553", "R_0805", "C_0805"):
            continue
        if ref.startswith("C") and int(ref[1:]) >= 101:
            continue  # cell capacitor is already connected above
        for pad in fp.Pads():
            if pad.GetNetname() != "/GND":
                continue
            x,y = pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)
            vx = x - 1.3 if ref in ("U2", "U3") else x + 1.35
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(mm(x,y)); t.SetEnd(mm(vx,y)); t.SetLayer(pcbnew.F_Cu)
            t.SetWidth(pcbnew.FromMM(.3)); t.SetNet(net); t.SetLocked(True); board.Add(t)
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(mm(vx,y)); v.SetWidth(pcbnew.FromMM(.6)); v.SetDrill(pcbnew.FromMM(.3))
            v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(net); v.SetLocked(True); board.Add(v)


def prepare_dsn(path):
    """Carry KiCad's real rules into DSN (its exporter omits edge clearance).

    The extra 0.325mm routing-only edge margin plus 0.2mm conductor clearance
    provides >0.5mm copper/edge clearance without weakening the project rules.
    Exported netclasses are also made explicit: 0.6mm power, 0.3mm signals.
    """
    text = path.read_text()
    def polygon(match):
        points = [float(n) for n in match.group(1).split()]
        if len(points) != 10:
            raise ValueError("Unexpected non-rectangular LED opening in DSN")
        xs, ys = points[0::2], points[1::2]
        x0,x1,y0,y1 = min(xs)-325,max(xs)+325,min(ys)-325,max(ys)+325
        coords = f'{x0:g} {y0:g} {x1:g} {y0:g} {x1:g} {y1:g} {x0:g} {y1:g} {x0:g} {y0:g}'
        return '(keepout "" (polygon signal 0 ' + coords + '))'
    text, count = re.subn(r'\(keepout "" \(polygon signal 0\s+([\d.\s-]+)\)\)', polygon, text)
    if count != 117:
        raise ValueError(f"Expected 117 DSN LED opening keepouts, got {count}")
    def boundary(match):
        points = [float(n) for n in match.group(1).split()]
        xs,ys = points[0::2],points[1::2]
        result = []
        for x,y in zip(xs,ys):
            result.extend([x+325 if x == min(xs) else x-325,
                           y+325 if y == min(ys) else y-325])
        return '(boundary (path pcb 0 ' + ' '.join(f'{n:g}' for n in result) + '))'
    text, count = re.subn(r'\(boundary\s+\(path pcb 0\s+([\d.\s-]+)\)\s*\)',boundary,text)
    if count != 1:
        raise ValueError("Expected one outer DSN boundary")
    text = re.sub(r'\(width 200\)', '(width 300)', text)
    power = ['/RAW_USB_5V','/FUSED_5V','/LED_5V','/GND']
    # On a fresh in-memory board KiCad may emit one default class; saved boards
    # correctly export the project's classes. Normalize either form, keeping
    # already-connected planes in their own class so the router can skip them.
    existing_power = re.search(r'^    \(class USB_LED_Power\b.*?^    \)', text, re.S | re.M)
    power_in_class = set()
    if existing_power:
        header = existing_power.group(0).split('(circuit',1)[0]
        power_in_class = set(header.split()[2:])
        if power_in_class != set(power):
            raise ValueError("Unexpected nets in exported power class")
        text = text[:existing_power.start()] + text[existing_power.end():]
    match = re.search(r'\(class kicad_default(.*?)\n\s+\(circuit',text,re.S)
    if not match:
        raise ValueError("Unexpected DSN default netclass")
    header = match.group(1)
    for net in power:
        header, count = re.subn(re.escape(net) + r'(?=\s|$)', '',header)
        if count + (net in power_in_class) != 1:
            raise ValueError(f"Power net missing or repeated in DSN: {net}")
    text = text[:match.start(1)] + header + text[match.end(1):]
    index = text.index('(class kicad_default')
    power_class = '''(class board_planes /GND /LED_5V
      (circuit (use_via "Via[0-3]_600:300_um"))
      (rule (width 600) (clearance 200)))
    (class usb_led_power /RAW_USB_5V /FUSED_5V
      (circuit (use_via "Via[0-3]_600:300_um"))
      (rule (width 600) (clearance 200)))
    '''
    text = text[:index] + power_class + text[index:]
    path.write_text(text)


def bulk_cap_connection(board):
    """Short, wide local connection from the pulse reservoir to U3's output.

    This is applied after session import as well as placement generation, so a
    preserved signal-routing session cannot drop the reservoir connection.
    """
    net = board.FindNet("/LED_5V")
    paths = [(pcbnew.In2_Cu, [(375.25,6),(375.25,3.8),(388,3.8),(388,12.4),(392.7,12.4)]),
             (pcbnew.F_Cu, [(392.7,12.4),(391.1375,12.4),(391.1375,13.05)])]
    existing = {(t.GetLayer(), t.GetNetCode(), t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)
                for t in board.GetTracks() if t.GetClass()=="PCB_TRACK"}
    for layer,points in paths:
        for a,b in zip(points,points[1:]):
            start,end = mm(*a),mm(*b)
            key = (layer,net.GetNetCode(),start.x,start.y,end.x,end.y)
            reverse = (layer,net.GetNetCode(),end.x,end.y,start.x,start.y)
            if key in existing or reverse in existing:
                continue
            t = pcbnew.PCB_TRACK(board); t.SetStart(start); t.SetEnd(end)
            t.SetLayer(layer); t.SetNet(net); t.SetWidth(pcbnew.FromMM(.6))
            t.SetLocked(True); board.Add(t)
    if not any(t.GetClass()=="PCB_VIA" and t.GetNetCode()==net.GetNetCode()
               and t.GetPosition()==mm(392.7,12.4) for t in board.GetTracks()):
        v = pcbnew.PCB_VIA(board); v.SetPosition(mm(392.7,12.4))
        v.SetWidth(pcbnew.FromMM(.7)); v.SetDrill(pcbnew.FromMM(.3))
        v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(net); v.SetLocked(True); board.Add(v)


def led_power_distribution(board, keys):
    """Low-impedance switched 5V pour with off-pad access for every LED/cap.

    Avoid a long serial power trace: a 117-pixel chain must not also be a chain
    of narrow supply bottlenecks. In1.Cu remains the uninterrupted GND return.
    """
    net = board.FindNet('/LED_5V')
    if not any(z.GetNetname()=='/LED_5V' for z in board.Zones()):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(pcbnew.F_Cu); zone.SetNet(net)
        zone.SetLocalClearance(pcbnew.FromMM(.25))
        zone.SetMinThickness(pcbnew.FromMM(.25))
        # Keep the off-pad vias/SMT power connections solid, but give the large
        # radial capacitor thermal relief so it can be hand-soldered normally.
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        zone.SetThermalReliefGap(pcbnew.FromMM(.3))
        zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(.4))
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        outline = zone.Outline(); outline.NewOutline()
        for x,y in ((.6,.6),(BOARD_W-.6,.6),(BOARD_W-.6,BOARD_H-.6),(.6,BOARD_H-.6)):
            outline.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
        board.Add(zone)
    for key in keys:
        x,y = key['x'],key['y']+5.08
        for a,b in [((x-3.05,y-.75),(x-4.35,y-.75)),
                    ((x+4.85,y),(x+4.85,y-1.75))]:
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(mm(*a)); track.SetEnd(mm(*b)); track.SetLayer(pcbnew.B_Cu)
            track.SetWidth(pcbnew.FromMM(.4)); track.SetNet(net)
            track.SetLocked(True); board.Add(track)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(mm(*b)); via.SetWidth(pcbnew.FromMM(.7))
            via.SetDrill(pcbnew.FromMM(.3)); via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
            via.SetNet(net); via.SetLocked(True); board.Add(via)


def generate_board(parts, keys, nets, report_dir, ses=None):
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetCopperLayerCount(4)
    board.GetTitleBlock().SetTitle("Cleaver - YD-RP2040 USB-C / 117 keys")
    board.GetTitleBlock().SetDate("2026-11-08")
    board.GetTitleBlock().SetRevision("0.3")
    ni = {}
    for name in sorted(set(nets.values())):
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item); ni[name] = item
    for a,b in [((0,0),(BOARD_W,0)),((BOARD_W,0),(BOARD_W,BOARD_H)),
                ((BOARD_W,BOARD_H),(0,BOARD_H)),((0,BOARD_H),(0,0))]:
        line(board, a,b,pcbnew.Edge_Cuts)
    for part in parts:
        kind, ref = part["kind"], part["ref"]
        fname = FP_NAMES.get(kind, kind)
        fp = pcbnew.FootprintLoad(str(PRETTY), fname)
        fp.SetFPID(pcbnew.LIB_ID("Cleaver", fname))
        fp.SetReference(ref); fp.SetValue(part["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + ident(ref)))
        fp.SetPosition(mm(part["x"], part["y"])); fp.SetOrientationDegrees(part["angle"])
        board.Add(fp)
        if part["back"]:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.Reference().SetVisible(kind == "MX" or ref in ("U1","U2","U3","F1","R1","TP1","C5"))
        fp.Value().SetVisible(False)
        if kind == "MX":
            fp.Reference().SetPosition(mm(part["x"], part["y"] + 8.4))
            fp.Reference().SetTextSize(mm(.8,.8)); fp.Reference().SetTextThickness(pcbnew.FromMM(.12))
        elif ref == "U1":
            fp.Reference().SetPosition(mm(part["x"],part["y"]))
        for pad in fp.Pads():
            key = (ref, str(pad.GetNumber()))
            if key in nets:
                expected = part["pins"].get(key[1])
                if expected is not None and nets[key].lstrip("/") != expected:
                    raise ValueError(f"Schematic net mismatch: {key} {expected} vs {nets[key]}")
                pad.SetNet(ni[nets[key]])
    for k in keys:
        x,y = k["x"], k["y"]
        for a,b in [((x-7,y-7),(x+7,y-7)),((x+7,y-7),(x+7,y+7)),
                    ((x+7,y+7),(x-7,y+7)),((x-7,y+7),(x-7,y-7))]:
            line(board,a,b,pcbnew.Dwgs_User)
    for text,x,y,layer in [("USB 5V TAP +",435,27,pcbnew.F_SilkS),
                           ("CLEAVER rev0.3 | USB-C | TP1: RAW USB VBUS",46,144.9,pcbnew.F_SilkS)]:
        label = pcbnew.PCB_TEXT(board)
        label.SetText(text); label.SetPosition(mm(x,y)); label.SetLayer(layer)
        label.SetTextSize(mm(.8,.8)); label.SetTextThickness(pcbnew.FromMM(.12)); board.Add(label)
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.In1_Cu); zone.SetNet(ni["/GND"])
    zone.SetLocalClearance(pcbnew.FromMM(.25)); zone.SetMinThickness(pcbnew.FromMM(.25))
    zone.SetThermalReliefGap(pcbnew.FromMM(.3)); zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(.4))
    outline = zone.Outline(); outline.NewOutline()
    for x,y in ((.6,.6),(BOARD_W-.6,.6),(BOARD_W-.6,BOARD_H-.6),(.6,BOARD_H-.6)):
        outline.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
    board.Add(zone)
    ground_fanout(board, keys, parts, ni["/GND"])
    led_power_distribution(board, keys)
    path = OUT / "Cleaver.kicad_pcb"
    pcbnew.SaveBoard(str(path), board)
    # Reload to apply the preserved project's fabrication rules and netclasses.
    board = pcbnew.LoadBoard(str(path))
    if ses:
        if not pcbnew.ImportSpecctraSES(board, str(ses)):
            raise RuntimeError("Failed to import routing session")
    bulk_cap_connection(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(path), board)
    if not ses:
        if not pcbnew.ExportSpecctraDSN(board, str(report_dir / "Cleaver.dsn")):
            raise RuntimeError("Failed to export routing input")
        prepare_dsn(report_dir / "Cleaver.dsn")


def generate_firmware(keys, leds):
    fw = OUT / "firmware"
    for path in (fw / "keymaps/default", fw / "keymaps/vial"):
        path.mkdir(parents=True, exist_ok=True)
    info = dict(keyboard_name="Cleaver", manufacturer="Cleaver keyboard project", maintainer="cleaver",
                processor="RP2040", bootloader="rp2040", diode_direction="ROW2COL",
                matrix_pins=dict(rows=ROW_GPIOS, cols=COL_GPIOS),
                usb=dict(vid="0xFEED", pid="0xC1EA", device_version="0.3.0", max_power=500),
                features=dict(bootmagic=True, extrakey=True, nkro=True, rgb_matrix=True),
                ws2812=dict(driver="vendor", pin=RGB_GPIO),
                rgb_matrix=dict(driver="ws2812", max_brightness=8, sleep=True,
                    layout=[dict(matrix=[k["matrix_row"], k["matrix_col"]],
                                 x=round(k["x"] / BOARD_W * 224), y=round(k["y"] / BOARD_H * 64), flags=4) for k in leds]),
                layouts=dict(LAYOUT=dict(layout=[dict(label=k["legend"], matrix=[k["matrix_row"], k["matrix_col"]],
                    x=round(k["x"] / U - k["w"] / 2,4), y=round(k["y"] / U - k["h"] / 2,4),
                    w=k["w"],h=k["h"]) for k in keys])))
    (fw / "keyboard.json").write_text(json.dumps(info, indent=2) + "\n")
    indicators = {name:next(k["led_index"] for k in keys if k["legend"] == legend)
                  for name,legend in (("CAPS","Caps Lock"),("NUM","Num Lock"),("SCROLL","Scroll Lock"))}
    (fw / "config.h").write_text('''#pragma once

// LED power MUST come from the raw USB VBUS tap at TP1, not module Vout.
// Keep the 8/255 cap until total current and rail voltage are measured.
#define RGB_MATRIX_DEFAULT_VAL 8
#define RGB_MATRIX_LED_COUNT 117
#define ENABLE_RGB_MATRIX_CYCLE_LEFT_RIGHT
#define ENABLE_RGB_MATRIX_SOLID_REACTIVE_SIMPLE
#define RGB_MATRIX_KEYPRESSES
#define WS2812_TIMING 1250
#define WS2812_T0H 350
#define WS2812_T1H 700
#define WS2812_TRST_US 280
#define LED_POWER_PIN GP28
''' + ''.join(f'#define CLEAVER_{name}_LED {index}\n' for name,index in indicators.items()))
    (fw / "rules.mk").write_text("BOARD = GENERIC_RP_RP2040\nBOOTLOADER = rp2040\n")
    codes = default_keycodes(keys)
    keymap = '#include QMK_KEYBOARD_H\n\nconst uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {\n    [0] = LAYOUT(\n'
    keymap += ",\n".join("        " + ", ".join(codes[i:i+8]) for i in range(0,len(codes),8)) + "\n    )\n};\n"
    for name in ("default", "vial"):
        (fw / f"keymaps/{name}/keymap.c").write_text(keymap)
    uid = uuid.uuid5(uuid.NAMESPACE_URL, "cleaver:YD-RP2040:0.3:vial").bytes[:8]
    unlock = [keys[0], next(k for k,c in zip(keys,codes) if c == "KC_ENT")]
    (fw / "keymaps/vial/config.h").write_text("#pragma once\n\n#define VIAL_KEYBOARD_UID { " +
        ", ".join(f"0x{b:02X}" for b in uid) + " }\n" +
        "#define VIAL_UNLOCK_COMBO_ROWS { " + ", ".join(str(k["matrix_row"]) for k in unlock) + " }\n" +
        "#define VIAL_UNLOCK_COMBO_COLS { " + ", ".join(str(k["matrix_col"]) for k in unlock) + " }\n")
    (fw / "keymaps/vial/rules.mk").write_text("VIA_ENABLE = yes\nVIAL_ENABLE = yes\nVIALRGB_ENABLE = yes\n")
    kle = []
    previous_y = 0
    for r in range(7):
        row, previous_x = [], 0
        for k in (k for k in keys if k["kle_row"] == r):
            left, top = k["x"] / U - k["w"] / 2, k["y"] / U - k["h"] / 2
            props = {"x": round(left - previous_x,4), "w":k["w"], "h":k["h"]}
            if not row:
                props["y"] = round(top - previous_y,4)
                previous_y = top + 1
            row.extend([props, f"{k['matrix_row']},{k['matrix_col']}"])
            previous_x = left + k["w"]
        kle.append(row)
    vial = dict(name="Cleaver", vendorId="0xFEED", productId="0xC1EA", lighting="vialrgb",
                matrix=dict(rows=8,cols=16), layouts=dict(keymap=kle))
    (fw / "keymaps/vial/vial.json").write_text(json.dumps(vial,indent=2) + "\n")
    with (fw / "key_matrix.csv").open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["ref","legend","matrix_row","matrix_col","plate_x_mm","plate_y_mm","rgb_chain_index"])
        for k in keys:
            writer.writerow([k["ref"],k["legend"],k["matrix_row"],k["matrix_col"],f"{k['x']:.4f}",f"{k['y']:.4f}",k["led_index"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--placement-only", action="store_true", help="Explicitly generate an unrouted board and DSN")
    parser.add_argument("--ses", type=Path, help="Import a routed session from this revision's DSN")
    parser.add_argument("--reports", type=Path, default=Path("/tmp/opencode/cleaver-revision"))
    args = parser.parse_args()
    if not args.placement_only and not args.ses:
        parser.error("Choose --placement-only or --ses FILE; never silently replace a routed board with an unrouted one")
    if args.ses and not args.ses.is_file():
        parser.error("Routing session does not exist")
    args.reports.mkdir(parents=True, exist_ok=True)
    keys, leds = read_keys()
    parts = components(keys, leds)
    write_footprints(); update_netclasses(); generate_schematic(parts, keys, leds)
    nets = schematic_nets(args.reports)
    generate_board(parts, keys, nets, args.reports, args.ses)
    generate_firmware(keys, leds)
    with (OUT / "BOM.csv").open("w",newline="") as file:
        writer = csv.writer(file, lineterminator="\n"); writer.writerow(["reference","value","footprint","x_mm","y_mm","side"])
        for p in parts:
            side = "F switch / B socket" if p["kind"]=="MX" else "B" if p["back"] else "F"
            writer.writerow([p["ref"],p["value"],FP_NAMES.get(p["kind"],p["kind"]),p["x"],p["y"],side])
    print(f"Generated revision 0.3: {len(keys)} unique keys, 8x16, 117 LEDs; " + ("session imported" if args.ses else "UNROUTED placement/DSN only"))


if __name__ == "__main__":
    main()
