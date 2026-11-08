#!/usr/bin/env python3
"""Generate the Cleaver keyboard KiCad project: a physical 7 x N grid matrix, a
Pico-form RP2040 module in the top-right corner with its USB connector flush with the
board edge, and a routed row/column grid, key diodes, and serpentine SK6812MINI-E LED
chain on a 4-layer stackup:

    F.Cu   : LED chain hops + LED_5V / GND row rails + data chain rails
    In1.Cu : column ladders (cathode rungs, per-cluster bus column) + fanout entries
    In2.Cu : row fanout lanes from the header pads down to each row bus
    B.Cu   : socket/diode pads, KEY wires, pad-1 stubs, ROW buses, power spines

The schematic is written as s-expressions; the PCB is built through the pcbnew API so
regeneration is deterministic and the user's Cleaver.kicad_pro is preserved. Geometry
constants were tuned so that DRC reports only real, reviewable clearances.
"""

from __future__ import annotations

import json
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

U = 19.05
BOARD_W, BOARD_H = 452.4375, 147.6375
N_ROWS = 7

# Switch cell geometry, relative to key centre (x right, y down).
SW_PAD_ROW = (6.29, -5.08)     # socket pad 1 (ROW), 2.55x2.5, B.Cu
SW_PAD_KEY = (-7.56, -2.54)    # socket pad 2 (KEY)
D_AN = (-1.15, -8.0)           # diode anode pad (1), KEY net
D_CA = (1.15, -8.0)            # diode cathode pad (2), COL net
LED_DX, LED_DY = 2.45, 6.5     # LED centre offset; pads 1.1x1.1 at (+-1,-1/+1)
LED_PAD = {1: (-1.0, -1.0), 2: (1.0, -1.0), 3: (1.0, 1.0), 4: (-1.0, 1.0)}
KEY_LINE = -9.4                # B.Cu KEY wire level
ROW_BUS_OFF = 8.9              # B.Cu row bus (below pads); last row uses -13.0
ROW_BUS_LAST = -13.0
COL_RUNG = -8.0                # In1 cathode rung level
BUS_CB = 1.55                  # column bus x = cluster LEFTMOST key centre + BUS_CB
COL_MAX_SPAN = 19.2
# Column bus sits between the anode east edge (+0.575) and the post-hole west edge
# (+1.04): a 0.15 mm track at +1.55..+2.31??  -> keep +1.55, 0.2 mm clearances.
W_COL = 0.2

# Column fanout corridor: the clear board strip south of row 6 LEDs (140.3..146.5).
# In1 COL entries run south from each ladder, then west along the strip, then north
# up the pad's lane column (In2 crossings pass because rows sit on In2/B only).
COL_FANOUT0 = 23.9
COL_FANOUT_STEP = 0.28
SPINE_5V = 451.6
SPINE_GND = 450.3

# Pico module placement (rot -90: odd pins north, even pins south, USB east at edge)
U1_CX, U1_CY = BOARD_W - 28.2, 13.39
GP_TO_PIN = {}
for _p, _g in {1:"GP0",2:"GP1",4:"GP2",5:"GP3",6:"GP4",7:"GP5",9:"GP6",10:"GP7",11:"GP8",
               12:"GP9",14:"GP10",15:"GP11",16:"GP12",17:"GP13",19:"GP14",20:"GP15",
               21:"GP16",22:"GP17",24:"GP18",25:"GP19",26:"GP20",27:"GP21",29:"GP22",
               31:"GP26",32:"GP27",34:"GP28"}.items():
    GP_TO_PIN[_g] = _p
GND_PINS = [3, 8, 13, 18, 23, 28, 33, 36]
UNUSED_PINS = {30:"RUN", 35:"ADC_VREF", 37:"3V3_EN", 38:"3V3_OUT", 39:"VSYS", 34:"GP28"}

W_SIG = 0.2
W_PWR = 0.5
W_GND = 0.4
FCU, BCU = pcbnew.F_Cu, pcbnew.B_Cu
IN1, IN2 = pcbnew.In1_Cu, pcbnew.In2_Cu


def pad_xy(pin):
    k = (pin - 1) // 2
    return U1_CX + 24.13 - 2.54 * k, U1_CY + (-8.89 if pin % 2 else 8.89)


def lane_x(pin):
    x, _ = pad_xy(pin)
    return x + 1.27 if pin == 1 else x - 1.27


def col_pin(ci):
    return GP_TO_PIN[f"GP{7 + ci}" if 7 + ci <= 22 else "GP26"]


def row_pin(r):
    return GP_TO_PIN[f"GP{r}"]


# ------------------------------------------------------------------ layout parsing

def read_keys():
    layout = json.loads((INPUT / "keyboard-layout(1).json").read_text())
    keys = []
    ybase = ycarry = 0.0
    for row_index, row in enumerate(layout):
        x = 0.0
        geom = {}
        for item in row:
            if isinstance(item, dict):
                geom.update(item)
                x += float(item.get("x", 0))
                ycarry += float(item.get("y", 0))
                continue
            w, h = float(geom.get("w", 1)), float(geom.get("h", 1))
            if not geom.get("d", False):
                keys.append({
                    "kle_row": row_index,
                    "legend": (item if item else "Space").replace("\n", "/"),
                    "x": (x + w / 2) * U,
                    "y": (ybase + ycarry + h / 2) * U,
                    "w": w, "h": h,
                })
            x += w
            geom = {}
        ybase += 1.0
    if len(keys) != 117:
        raise ValueError(f"Expected 117 switch positions, got {len(keys)}")

    for k in keys:
        k["matrix_row"] = k["kle_row"]

    centres = sorted({round(k["x"], 4) for k in keys})
    clusters, cur = [], [centres[0]]
    for cx in centres[1:]:
        if cx - cur[0] <= COL_MAX_SPAN:
            cur.append(cx)
        else:
            clusters.append(cur)
            cur = [cx]
    clusters.append(cur)
    centre_to_col = {cx: ci for ci, cl in enumerate(clusters) for cx in cl}
    for k in keys:
        k["matrix_col"] = centre_to_col[round(k["x"], 4)]
        k["bus_x"] = clusters[k["matrix_col"]][0] + BUS_CB
    n_cols = len(clusters)
    if n_cols > 18:
        raise ValueError(f"{n_cols} column clusters exceed the GPIO budget")

    for i, k in enumerate(keys):
        k["ref"] = f"SW{i+1:03d}"
        k["diode"] = f"D{i+1:03d}"
        k["key_net"] = f"KEY{i:03d}"
        k["led_ref"] = f"LED{i+1:03d}"

    led_order = []
    for r in range(N_ROWS):
        rk = [k for k in keys if k["kle_row"] == r]
        rk.sort(key=lambda k: k["x"], reverse=bool(r % 2))
        led_order.extend(rk)
    for i, k in enumerate(led_order):
        k["led_index"] = i
        k["rgb_in"] = f"RGB_CHAIN_{i:03d}"
        k["rgb_out"] = f"RGB_CHAIN_{i + 1:03d}"
    return keys, led_order, n_cols


# ------------------------------------------------------------------ footprints

FOOTPRINTS = {
    "SK6812MINI-E": """(module SK6812MINI-E (layer F.Cu) (tedit 0)
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
)""",
    "D_SOD-123": """(module D_SOD-123 (layer F.Cu) (tedit 0)
  (descr "1N4148W SOD-123 switching diode") (tags "SOD-123 diode") (attr smd)
  (fp_text reference REF** (at 0 -1.8) (layer F.SilkS) (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value D_SOD-123 (at 0 1.8) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.55 -1.05) (end 1.55 1.05) (layer F.Fab) (width 0.1))
  (fp_line (start 0.2 -1.05) (end 0.2 1.05) (layer F.Fab) (width 0.12))
  (pad 1 smd rect (at -1.15 0) (size 1.15 1.25) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1.15 0) (size 1.15 1.25) (layers F.Cu F.Paste F.Mask))
)""",
    "R_0603": """(module R_0603 (layer F.Cu) (tedit 0) (descr "0603 resistor") (tags "0603 resistor") (attr smd)
  (fp_text reference REF** (at 0 -1.4) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_text value R_0603 (at 0 1.4) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -0.8 -0.45) (end 0.8 0.45) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -0.8 0) (size 0.9 1) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 0.8 0) (size 0.9 1) (layers F.Cu F.Paste F.Mask))
)""",
    "PTC_1206": """(module PTC_1206 (layer F.Cu) (tedit 0) (descr "1206 resettable fuse") (tags "1206 PTC fuse") (attr smd)
  (fp_text reference REF** (at 0 -1.6) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_text value PTC_1206 (at 0 1.6) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.7 -0.9) (end 1.7 0.9) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -1.2 0) (size 1.1 1.4) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at 1.2 0) (size 1.1 1.4) (layers F.Cu F.Paste F.Mask))
)""",
    "C_Radial_D8": """(module C_Radial_D8 (layer F.Cu) (tedit 0) (descr "Radial electrolytic capacitor, 8mm body") (tags "radial capacitor") (attr through_hole)
  (fp_text reference REF** (at 0 -5) (layer F.SilkS) (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text value C_Radial_D8 (at 0 5) (layer F.Fab) (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_circle (center 0 0) (end 4 0) (layer F.Fab) (width 0.12))
  (fp_line (start -4 0) (end 4 0) (layer F.Fab) (width 0.12))
  (pad 1 thru_hole circle (at -1.75 0) (size 1.8 1.8) (drill 0.8) (layers *.Cu *.Mask))
  (pad 2 thru_hole circle (at 1.75 0) (size 1.8 1.8) (drill 0.8) (layers *.Cu *.Mask))
)""",
    "AHCT1G125_SOT23-5": """(module AHCT1G125_SOT23-5 (layer F.Cu) (tedit 0) (descr "74AHCT1G125 single buffer SOT-23-5") (tags "SOT-23-5 buffer") (attr smd)
  (fp_text reference REF** (at 0 -2.4) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_text value AHCT1G125 (at 0 2.4) (layer F.Fab) (effects (font (size 0.7 0.7) (thickness 0.1))))
  (fp_rect (start -1.5 -1.1) (end 1.5 1.1) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -2.0 -0.65) (size 1.2 0.45) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at -2.0 0) (size 1.2 0.45) (layers F.Cu F.Paste F.Mask))
  (pad 3 smd rect (at -2.0 0.65) (size 1.2 0.45) (layers F.Cu F.Paste F.Mask))
  (pad 4 smd rect (at 2.0 0.65) (size 1.2 0.6) (layers F.Cu F.Paste F.Mask))
  (pad 5 smd rect (at 2.0 -0.65) (size 1.2 0.6) (layers F.Cu F.Paste F.Mask))
)""",
}


def pico_footprint():
    pads = []
    for i in range(20):
        y = -24.13 + 2.54 * i
        pads.append(f'  (pad {2*i+1} thru_hole circle (at -8.89 {y:.2f}) (size 1.8 1.8) (drill 1.0) (layers *.Cu *.Mask))')
        pads.append(f'  (pad {2*i+2} thru_hole circle (at 8.89 {y:.2f}) (size 1.8 1.8) (drill 1.0) (layers *.Cu *.Mask))')
    return ('(module RP2040_Pico_Header (layer F.Cu) (tedit 0)\n'
            '  (descr "Raspberry Pi Pico form-factor RP2040 module, 2x20 header footprint, 2.54mm pitch")\n'
            '  (tags "Raspberry Pi Pico RP2040 module") (attr through_hole)\n'
            '  (fp_text reference REF** (at 0 -27.5) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))\n'
            '  (fp_text value RP2040_Pico (at 0 27.5) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n'
            '  (fp_rect (start -10.5 -25.4) (end 10.5 25.4) (layer F.Fab) (width 0.15))\n'
            '  (fp_rect (start -10.5 -28.2) (end 10.5 -23.5) (layer F.Fab) (width 0.15))\n'
            + "\n".join(pads) + "\n)\n")


def write_custom_footprints():
    PRETTY.mkdir(parents=True, exist_ok=True)
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
    for name, text in FOOTPRINTS.items():
        (PRETTY / f"{name}.kicad_mod").write_text(text)
    (PRETTY / "RP2040_Pico_Header.kicad_mod").write_text(pico_footprint())


# ------------------------------------------------------------------ board primitives

NET_CODES = {}
NET_ITEMS = {}


def add_net(board, names):
    codes, items = {}, {}
    for name in names:
        board_name = name if name.startswith("unconnected-") else f"/{name}"
        net = pcbnew.NETINFO_ITEM(board, board_name)
        board.Add(net)
        codes[name] = net.GetNetCode()
        items[name] = net
    return codes, items


def load_fp(name):
    fp = pcbnew.FootprintLoad(str(PRETTY), name)
    if fp is None:
        raise RuntimeError(f"Could not load footprint {name}")
    return fp


def component_uuid(ref):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cleaver-keyboard:{ref}"))


def assign_pad_nets(fp, pads):
    for pad in fp.Pads():
        net = pads.get(str(pad.GetNumber()))
        if net:
            pad.SetNetCode(NET_CODES[net])


def place_fp(board, name, ref, value, x, y, angle=0, pads=None, back=False):
    fp = load_fp(name)
    fp.SetFPID(pcbnew.LIB_ID("Cleaver", name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientationDegrees(angle)
    if not back:
        fp.SetLayer(pcbnew.F_Cu)
    fp.SetPath(pcbnew.KIID_PATH("/" + component_uuid(ref)))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    board.Add(fp)
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
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


def via(board, x, y, net, size=0.6, drill=0.3):
    if net is None:
        return
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(size))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetNet(NET_ITEMS[net])
    board.Add(v)
    return v


def track(board, x1, y1, x2, y2, layer, net, width=W_SIG):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(width))
    t.SetLayer(layer)
    t.SetNet(NET_ITEMS[net])
    board.Add(t)
    return t


def tpoly(board, pts, layer, net, width=W_SIG):
    for a, b in zip(pts, pts[1:]):
        track(board, a[0], a[1], b[0], b[1], layer, net, width)


# ------------------------------------------------------------------ routing

def route_pcb(board, keys, led_order, n_cols):
    row_groups = defaultdict(list)
    col_groups = defaultdict(list)
    for k in keys:
        row_groups[k["matrix_row"]].append(k)
        col_groups[k["matrix_col"]].append(k)

    # ---- KEY wire (B.Cu): pad 2 -> north -> east above the diode -> anode
    for k in keys:
        cx, cy = k["x"], k["y"]
        tpoly(board, [
            (cx + SW_PAD_KEY[0], cy + SW_PAD_KEY[1]),
            (cx + SW_PAD_KEY[0], cy + KEY_LINE),
            (cx + D_AN[0], cy + KEY_LINE),
            (cx + D_AN[0], cy - 8.0),
        ], BCU, k["key_net"], W_SIG)

    # ---- ROW buses (B.Cu) + pad-1 stubs, extended east to each row's fanout lane
    for r in range(N_ROWS):
        net = f"ROW{r}"
        kset = sorted(row_groups[r], key=lambda k: k["x"])
        cy = kset[0]["y"]
        by = cy + ROW_BUS_LAST if r == 6 else cy + ROW_BUS_OFF
        lane = lane_x(row_pin(r))
        east = 449.54 if r == 0 else lane + 0.4
        track(board, kset[0]["x"] + SW_PAD_ROW[0] - 0.4, by, east, by, BCU, net, W_SIG)
        for k in kset:
            px = k["x"] + SW_PAD_ROW[0]
            track(board, px, k["y"] + SW_PAD_ROW[1], px, by, BCU, net, W_SIG)

    # ---- ROW fanout (In2): pad -> lane between pad columns -> south to bus -> via
    for r in range(N_ROWS):
        net = f"ROW{r}"
        kset = row_groups[r]
        by = kset[0]["y"] + (ROW_BUS_LAST if r == 6 else ROW_BUS_OFF)
        pin = row_pin(r)
        pad_px, pad_py = pad_xy(pin)
        lane = lane_x(pin)
        tpoly(board, [(pad_px, pad_py), (lane, pad_py), (lane, by)], IN2, net, W_SIG)
        via(board, lane, by, net)

    # ---- COL ladders (In1) + fanout entries
    for ci in range(n_cols):
        net = f"COL{ci:02d}"
        kset = sorted(col_groups[ci], key=lambda k: k["y"])
        bx = kset[0]["bus_x"]
        for i, k in enumerate(kset):
            vy = k["y"] + COL_RUNG
            via(board, k["x"] + D_CA[0], vy, net)
            track(board, k["x"] + D_CA[0], vy, bx, vy, IN1, net, W_COL)      # rung west
            if i + 1 < len(kset):
                track(board, bx, vy, bx, kset[i + 1]["y"] + COL_RUNG, IN1, net, W_COL)
        # fanout entry: south from the topmost rung outside the key field (bus column
        # between rightmost LED east extent and the spine), into the bottom strip,
        # then north up the pad's lane column onto the pad row level, and east to pad.
        pin = col_pin(ci)
        pad_px, pad_py = pad_xy(pin)
        lane = pad_px - 1.27
        fy = COL_FANOUT0 + COL_FANOUT_STEP * ci
        top = kset[0]
        tpoly(board, [(bx, top["y"] + COL_RUNG), (bx, fy)], IN1, net, W_COL)
        if pad_py < 12:
            # N-row pin: fy hop down, then west/east in the between-pad lane, north
            # on IN1 (crossing the pad rows through the gap between pad columns),
            # then a B.Cu hop under the pad onto its south edge.
            via(board, bx, fy, net)
            tpoly(board, [(bx, fy), (lane, fy)], BCU, net, W_COL)
            via(board, lane, fy, net)
            tpoly(board, [(lane, fy), (lane, 6.2)], IN1, net, W_COL)
            via(board, lane, 6.2, net)
            tpoly(board, [(lane, 6.2), (pad_px, 6.2), (pad_px, pad_py)], BCU, net, W_COL)
        else:
            via(board, bx, fy, net)
            tpoly(board, [(bx, fy), (pad_px, fy), (pad_px, pad_py)], BCU, net, W_COL)

    # ---- LED chain (F.Cu hops on pads + B.Cu rails) and power rails
    for i, k in enumerate(led_order):
        lx, ly = k["x"] + LED_DX, k["y"] + LED_DY
        r6 = k["kle_row"] == 6
        via(board, lx + LED_PAD[1][0], ly + LED_PAD[1][1], "LED_5V")
        via(board, lx + LED_PAD[3][0], ly + LED_PAD[3][1], "GND")
        via(board, lx + LED_PAD[4][0], ly + LED_PAD[4][1], k["rgb_in"])
        if i < len(led_order) - 1:
            via(board, lx + LED_PAD[2][0], ly + LED_PAD[2][1], k["rgb_out"])

    led_by_row = defaultdict(list)
    for k in led_order:
        led_by_row[k["kle_row"]].append(k)
    RAIL_5V = 2.8
    for r, ks in led_by_row.items():
        ks = sorted(ks, key=lambda k: k["x"])
        y_row = ks[0]["y"]
        x_w = ks[0]["x"] + LED_DX - 1.85
        x_e = ks[-1]["x"] + LED_DX + 1.85
        track(board, x_w, y_row + RAIL_5V, x_e, y_row + RAIL_5V, FCU, "LED_5V", W_PWR)
        track(board, x_w, y_row + LED_DY + 2.1, x_e, y_row + LED_DY + 2.1, FCU, "GND", W_GND)
    # data chain rails (B.Cu) at the DOUT pad row
    for k1, k2 in zip(led_order, led_order[1:]):
        net = k1["rgb_out"]
        y1 = k1["y"] + LED_DY - 1.0          # DOUT pad row
        y2 = k2["y"] + LED_DY + 1.0          # DIN pad row
        x1 = k1["x"] + LED_DX + 1.0
        x2 = k2["x"] + LED_DX - 1.0
        if abs(y1 - y2) < 1:
            yc = y1 + 1.0            # between-pad-row chain level (IN2)
            track(board, x1, y1, x1, yc, IN2, net, W_SIG)
            track(board, x1, yc, x2, y2 - 1.0, IN2, net, W_SIG)
            track(board, x2, y2 - 1.0, x2, y2 + 1.0, IN2, net, W_SIG)
            track(board, x2, y2 + 1.0, x2, y2, IN2, net, W_SIG)
        else:
            x = max(x1, x2) + 1.2 if k1["x"] > k2["x"] else min(x1, x2) - 1.2
            tpoly(board, [(x1, y1), (x, y1), (x, y2), (x2, y2)], IN2, net, W_SIG)
    # spine taps
    for r, ks in led_by_row.items():
        y_row = ks[0]["y"]
        x_e = max(k["x"] for k in ks) + LED_DX + 1.85
        track(board, x_e, y_row + RAIL_5V, SPINE_5V, y_row + RAIL_5V, FCU, "LED_5V", W_PWR)
        via(board, SPINE_5V, y_row + RAIL_5V, "LED_5V")
        track(board, x_e, y_row + LED_DY + 2.1, SPINE_GND, y_row + LED_DY + 2.1, FCU, "GND", W_GND)
        via(board, SPINE_GND, y_row + LED_DY + 2.1, "GND")
    track(board, SPINE_5V, 1.9, SPINE_5V, 114.3 + RAIL_5V, IN1, "LED_5V", W_PWR)
    track(board, SPINE_GND, 3.5, SPINE_GND, 114.3 + LED_DY + 1.0, IN1, "GND", W_GND)


def place_corner_circuit(board):
    place_fp(board, "PTC_1206", "F1", "PTC 0.5A hold", 400.0, 3.5,
             pads={"1": "USB_5V", "2": "LED_5V"})
    place_fp(board, "C_Radial_D8", "C1", "470uF 6.3V", 412.0, 3.5,
             pads={"1": "LED_5V", "2": "GND"})
    place_fp(board, "AHCT1G125_SOT23-5", "U2", "74AHCT1G125", 444.0, 28.5,
             pads={"1": "GND", "2": "RGB_DATA", "3": "GND", "4": "RGB_BUF", "5": "LED_5V"})
    place_fp(board, "R_0603", "R1", "330R", 385.0, 143.0,
             pads={"1": "RGB_BUF", "2": "RGB_CHAIN_000"})


def route_corner(board, led_order):
    # USB_5V: VBUS pad 40 -> F1 pad 1 (B.Cu)
    p40x, p40y = pad_xy(40)
    tpoly(board, [(p40x, p40y), (400.0 - 1.2, p40y), (400.0 - 1.2, 3.5)], BCU, "USB_5V", W_PWR)
    # LED_5V node: F1 pad 2, C1 pad 1, U2 pad 5, spine
    via(board, 401.2, 3.5, "LED_5V")
    via(board, 410.25, 3.5, "LED_5V")
    track(board, 401.2, 3.5, 410.25, 3.5, BCU, "LED_5V", W_PWR)
    track(board, 401.2, 3.5, 401.2, 2.0, BCU, "LED_5V", W_PWR)
    via(board, 401.2, 2.0, "LED_5V")
    track(board, 401.2, 2.0, SPINE_5V, 2.0, IN1, "LED_5V", W_PWR)
    via(board, 446.0, 27.85, "LED_5V")
    tpoly(board, [(446.0, 27.85), (451.6, 27.85)], IN1, "LED_5V", W_PWR)
    # GND node: C1 pad 2 + U2 pads 1/3 to the spine
    via(board, 413.75, 3.5, "GND")
    track(board, 413.75, 3.5, 413.75, 1.6, BCU, "GND", W_GND)
    via(board, 413.75, 1.6, "GND")
    track(board, 413.75, 1.6, SPINE_GND, 1.6, IN1, "GND", W_GND)
    via(board, 401.2, 3.5, "LED_5V")
    via(board, 442.0, 27.85, "GND")
    via(board, 442.0, 29.15, "GND")
    tpoly(board, [(442.0, 29.15), (442.7, 29.15), (442.7, 31.36), (449.9, 31.36)], BCU, "GND", W_GND)
    via(board, 449.9, 31.36, "GND")
    track(board, 449.9, 31.36, SPINE_GND, 31.36, IN1, "GND", W_GND)
    track(board, 442.0, 27.85, 441.3, 27.85, FCU, "GND", W_GND)
    via(board, 441.3, 27.85, "GND")
    track(board, 441.3, 27.85, 441.3, 30.2, BCU, "GND", W_GND)
    # RGB_DATA: GP27 pad 32 -> U2 pad 2 (442.0, 28.5)
    p32x, p32y = pad_xy(GP_TO_PIN["GP27"])
    tpoly(board, [(p32x, p32y), (p32x, 31.75), (440.4, 31.75)], BCU, "RGB_DATA", W_SIG)
    via(board, 440.4, 31.75, "RGB_DATA")
    tpoly(board, [(440.4, 31.75), (442.0, 31.75), (442.0, 28.5)], FCU, "RGB_DATA", W_SIG)
    # RGB_BUF: U2 pad 4 (446.0, 29.15) -> south to the strip -> R1 pad 1 (384.2, 143.0)
    tpoly(board, [(446.0, 29.15), (447.0, 29.15), (447.0, 139.0), (384.2, 139.0),
                  (384.2, 143.0)], FCU, "RGB_BUF", W_SIG)
    via(board, 447.0, 29.15, "RGB_BUF")
    # R1 pad 2 (385.8, 143.0) -> LED 1 DIN (RGB_CHAIN_000), LED 1 = top-left key
    k0 = led_order[0]
    d0x, d0y = k0["x"] + LED_DX + LED_PAD[4][0], k0["y"] + LED_DY + LED_PAD[4][1]
    tpoly(board, [(385.8, 143.0), (448.0, 143.0), (448.0, 139.8), (d0x, 139.8), (d0x, d0y)],
          FCU, "RGB_CHAIN_000", W_SIG)
    via(board, 448.0, 143.0, "RGB_CHAIN_000")
    via(board, d0x, d0y, "RGB_CHAIN_000")


# ------------------------------------------------------------------ board assembly

def generate_board(keys, led_order, n_cols):
    global NET_CODES, NET_ITEMS
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    # fab-appropriate minimums for a 4-layer JLC-style board
    ds.m_MinTrackWidth = pcbnew.FromMM(0.15)
    ds.m_MinViaDia = pcbnew.FromMM(0.45)
    ds.m_MinViaDrill = pcbnew.FromMM(0.2)
    ds.m_MinHoleSize = pcbnew.FromMM(0.2)
    ds.m_MinHoleToHole = pcbnew.FromMM(0.2)
    ds.m_MinClearance = pcbnew.FromMM(0.15)
    ds.m_MinEdgeClearance = pcbnew.FromMM(0.2)
    try:
        stack = ds.GetEnabledLayers()
        for lid in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            if not stack.Test(lid):
                stack.AddRaw(1 << lid)
        ds.SetEnabledLayers(stack)
    except Exception:
        pass
    board.GetTitleBlock().SetTitle("Cleaver full-size keyboard")
    board.GetTitleBlock().SetDate("2026-11-07")
    board.GetTitleBlock().SetRevision("0.2 - routed grid prototype, 4-layer")

    net_names = ["GND", "USB_5V", "LED_5V", "RGB_DATA", "RGB_BUF"]
    net_names += [f"ROW{r}" for r in range(N_ROWS)]
    net_names += [f"COL{ci:02d}" for ci in range(n_cols)]
    net_names += [k["key_net"] for k in keys]
    net_names += [f"RGB_CHAIN_{i:03d}" for i in range(len(led_order) + 1)]
    for pin, name in UNUSED_PINS.items():
        net_names.append(f"unconnected-(U1-{name}-Pad{pin})")
    net_names.append("unconnected-(LED117-DOUT-Pad2)")
    NET_CODES, NET_ITEMS = add_net(board, net_names)

    add_rect(board, 0, 0, BOARD_W, BOARD_H, pcbnew.Edge_Cuts, 0.05)
    for k in keys:
        add_rect(board, k["x"] - 7, k["y"] - 7, 14, 14)
    for x, y, w, h in parse_dxf_slots():
        add_rect(board, x, y, w, h)

    pico_pads = {}
    for r in range(N_ROWS):
        pico_pads[str(row_pin(r))] = f"ROW{r}"
    for ci in range(n_cols):
        pico_pads[str(col_pin(ci))] = f"COL{ci:02d}"
    pico_pads[str(GP_TO_PIN["GP27"])] = "RGB_DATA"
    for pin, name in UNUSED_PINS.items():
        pico_pads[str(pin)] = f"unconnected-(U1-{name}-Pad{pin})"
    for pin in GND_PINS:
        pico_pads[str(pin)] = "GND"
    pico_pads["40"] = "USB_5V"
    place_fp(board, "RP2040_Pico_Header", "U1", "Raspberry Pi Pico / RP2040", U1_CX, U1_CY, -90,
             pads=pico_pads)

    for k in keys:
        place_fp(board, "Kailh_socket_MX", k["ref"], k["legend"], k["x"], k["y"],
                 pads={"1": f"ROW{k['matrix_row']}", "2": k["key_net"]})
        place_fp(board, "D_SOD-123", k["diode"], "1N4148W", k["x"], k["y"] - 8.0,
                 back=True, pads={"1": k["key_net"], "2": f"COL{k['matrix_col']:02d}"})
    for k in led_order:
        place_fp(board, "SK6812MINI-E", k["led_ref"], f"RGB {k['legend']}",
                 k["x"] + LED_DX, k["y"] + LED_DY,
                 pads={"1": "LED_5V",
                       "2": ("unconnected-(LED117-DOUT-Pad2)"
                             if k["led_index"] == len(led_order) - 1 else k["rgb_out"]),
                       "3": "GND", "4": k["rgb_in"]})

    place_corner_circuit(board)
    route_pcb(board, keys, led_order, n_cols)
    route_corner(board, led_order)

    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(f"CLEAVER - 117 MX / SK6812MINI-E - {N_ROWS}x{n_cols} ROUTED GRID - 4L")
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(3), pcbnew.FromMM(144.9)))
    txt.SetLayer(pcbnew.Dwgs_User)
    txt.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
    txt.SetTextThickness(pcbnew.FromMM(0.15))
    board.Add(txt)

    OUT.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(OUT / f"{NAME}.kicad_pcb"), board)


def parse_dxf_slots():
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
        block = entities[i:i + 8]
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


# ------------------------------------------------------------------ schematic (s-expressions)

def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


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


PICO_NAMES = {
    1:"GP0", 2:"GP1", 3:"GND", 4:"GP2", 5:"GP3", 6:"GP4", 7:"GP5", 8:"GND",
    9:"GP6", 10:"GP7", 11:"GP8", 12:"GP9", 13:"GND", 14:"GP10", 15:"GP11", 16:"GP12",
    17:"GP13", 18:"GND", 19:"GP14", 20:"GP15", 21:"GP16", 22:"GP17", 23:"GND", 24:"GP18",
    25:"GP19", 26:"GP20", 27:"GP21", 28:"GND", 29:"GP22", 30:"RUN", 31:"GP26", 32:"GP27",
    33:"AGND", 34:"GP28", 35:"ADC_VREF", 36:"GND", 37:"3V3_EN", 38:"3V3_OUT", 39:"VSYS", 40:"VBUS",
}


def pico_pins():
    pins = []
    for i in range(20):
        y = 24.13 - i * 2.54
        pins.append(pin_def(2 * i + 1, PICO_NAMES[2 * i + 1], -25.4, y, 0, length=5.08))
        pins.append(pin_def(2 * i + 2, PICO_NAMES[2 * i + 2], 25.4, y, 180, length=5.08))
    return pins


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


def schematic_label(name, x, y, side="right"):
    angle = 0 if side == "right" else 180
    justify = "left" if side == "right" else "right"
    return f'''  (label {q(name)} (at {x:.4f} {y:.4f} {angle})
    (effects (font (size 0.9 0.9)) (justify {justify} bottom))
    (uuid {uuid.uuid4()}))'''


def schematic_no_connect(x, y):
    return f'  (no_connect (at {x:.4f} {y:.4f}) (uuid {uuid.uuid4()}))'


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
        lines.append(f'    (pin {q(str(pin))} (uuid {uuid.uuid4()}))')
    lines.append('  )')
    return ident, "\n".join(lines)


def generate_schematic(keys, led_order, n_cols):
    library = symbol_definitions(qualified=True)
    symbols, labels, texts, instances, no_connects = [], [], [], [], []

    def add_component(lib, ref, value, fp, x, y, pins):
        ident, text = schematic_component(lib, ref, value, fp, x, y, pins)
        symbols.append(text)
        instances.append(f'''    (path "/{ident}" (reference {q(ref)}) (unit 1) (value {q(value)}) (footprint {q(fp)}))''')

    cell_seen = defaultdict(int)
    for k in keys:
        row, col = k["matrix_row"], k["matrix_col"]
        sub = cell_seen[(row, col)]
        cell_seen[(row, col)] += 1
        x, y = 31.75 + col * 25.4, 41.91 + row * 25.4 + sub * 6.35
        dx = x + 12.7
        add_component("Cleaver:KeySwitch", k["ref"], k["legend"], "Cleaver:Kailh_socket_MX", x, y, [1, 2])
        add_component("Cleaver:KeyDiode", k["diode"], "1N4148W", "Cleaver:D_SOD-123", dx, y, [1, 2])
        labels += [
            schematic_label(f"ROW{row}", x - 5.08, y, "left"),
            schematic_label(k["key_net"], x + 5.08, y, "right"),
            schematic_label(k["key_net"], dx - 5.08, y, "left"),
            schematic_label(f"COL{col:02d}", dx + 5.08, y, "right"),
        ]
        texts.append(schematic_text(k["legend"][:16], x + 3, y + 7.4, 0.7))

    led_grid_cols = 6
    for i, k in enumerate(led_order):
        row, col = divmod(i, led_grid_cols)
        x, y = 508 + col * 25.4, 43.18 + row * 22.86
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

    px, py = 704.85, 198.12
    add_component("Cleaver:PicoModule", "U1", "Raspberry Pi Pico / RP2040", "Cleaver:RP2040_Pico_Header", px, py, range(1, 41))
    gpio_nets = {f"GP{r}": f"ROW{r}" for r in range(N_ROWS)}
    for ci in range(n_cols):
        gpio_nets[f"GP{7 + ci}" if 7 + ci <= 22 else "GP26"] = f"COL{ci:02d}"
    gpio_nets["GP27"] = "RGB_DATA"
    for pin_number, pin_name in PICO_NAMES.items():
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
        else:
            no_connects.append(schematic_no_connect(lx, ly))

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
  (uuid {uuid.uuid4()})
  (paper "A1")
  (title_block (title "Cleaver full-size keyboard") (date "2026-11-07") (rev "0.2 - routed grid prototype"))
  (lib_symbols
{library}
  )
'''
    body = [
        schematic_text(f"CLEAVER - 117 MX HOT-SWAP KEYS / {N_ROWS} x {n_cols} PHYSICAL GRID", 35, 20, 2.0),
        schematic_text("Diodes: ROW2COL. U1 is a Pico-form RP2040 module placed top-right, USB at the board edge.", 35, 26, 1.0),
        schematic_text("RGB: 117 x SK6812MINI-E, serpentine order. USB-only: 500mA PTC and QMK brightness cap 12/255.", 35, 31, 1.0),
        schematic_text("Rows = physical key rows GP0-GP6; columns GP7-GP22/GP26; RGB data GP27; GP28 spare.", 35, 36, 1.0),
    ] + texts + labels + no_connects + symbols
    header += "\n".join(body)
    header += f'''\n  (sheet_instances (path "/" (page "1")))
  (symbol_instances
{chr(10).join(instances)}
  )
  (embedded_fonts no)
)\n'''
    (OUT / f"{NAME}.kicad_sch").write_text(header)


def generate_tables_and_symbols():
    (OUT / "fp-lib-table").write_text('''(fp_lib_table
  (lib (name "Cleaver") (type "KiCad") (uri "${KIPRJMOD}/Cleaver.pretty") (options "") (descr "Project-local Cleaver keyboard footprints"))
)
''')
    (OUT / "sym-lib-table").write_text('''(sym_lib_table
  (lib (name "Cleaver") (type "KiCad") (uri "${KIPRJMOD}/Cleaver.kicad_sym") (options "") (descr "Project-local Cleaver keyboard symbols"))
)
''')
    (OUT / "Cleaver.kicad_sym").write_text(
        '(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n' +
        symbol_definitions(qualified=False) + '\n)\n'
    )


# ------------------------------------------------------------------ firmware + docs

def generate_firmware_files(keys, led_order, n_cols):
    fw = OUT / "firmware"
    fw.mkdir(exist_ok=True)
    row_pins = [f"GP{i}" for i in range(N_ROWS)]
    col_pins = ([f"GP{i}" for i in range(7, 23)] + ["GP26"])[:n_cols]
    qmk = {
        "keyboard_name": "Cleaver",
        "manufacturer": "Cleaver keyboard project",
        "maintainer": "cleaver",
        "processor": "RP2040",
        "bootloader": "rp2040",
        "matrix_pins": {"rows": row_pins, "cols": col_pins},
        "diode_direction": "ROW2COL",
        "usb": {"vid": "0xFEED", "pid": "0xC1EA", "device_version": "0.2.0"},
        "rgb_matrix": {
            "driver": "ws2812",
            "max_brightness": 12,
            "layout": [
                {
                    "matrix": [k["matrix_row"], k["matrix_col"]],
                    "x": round(k["x"] / BOARD_W * 224, 2),
                    "y": round(k["y"] / BOARD_H * 64, 2),
                    "flags": 1,
                }
                for k in led_order
            ],
        },
    }
    (fw / "keyboard.json").write_text(json.dumps(qmk, indent=2) + "\n")
    (fw / "config.h").write_text(f"""#pragma once

#define MATRIX_ROWS {N_ROWS}
#define MATRIX_COLS {n_cols}
#define MATRIX_ROW_PINS {{ {", ".join(row_pins)} }}
#define MATRIX_COL_PINS {{ {", ".join(col_pins)} }}
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


def write_readme(n_cols):
    (OUT / "README.md").write_text(f"""# Cleaver KiCad project

Generated from the supplied KLE JSON and plate DXF by `scripts/generate_kicad.py`:
**117 MX switch positions** (Kailh MX hotswap sockets), one 1N4148W diode per key
(ROW2COL), and **117 SK6812MINI-E RGB pixels** in a serpentine chain. The three
lock-indicator graphics in the KLE are decals, not footprints.

## Controller and USB access

The controller is a Raspberry Pi Pico form-factor RP2040 module on a soldered 2x20,
2.54 mm header footprint, in the **top-right corner with its USB connector flush with
the right board edge**, so the cable plugs straight in from the edge. The stock Pico is
micro-USB; if you want USB-C at that edge, buy the same outline with a USB-C
receptacle (several Pico-pinout modules offer this) or move to the bare-RP2040 +
board-mounted USB-C jack topology (what the 4-layer full-size reference designs use).
The Pico footprint is deliberate here: it is what exposes all 26 usable GPIOs the
7 x {n_cols} grid needs; Pro Micro-style footprints do not.

## Matrix and routing

Typical custom-QMK physical grid: **{N_ROWS} row wires** (the seven key rows, GP0-GP6)
x **{n_cols} column wires** (GP7-GP22, GP26), RGB data GP27, GP28 spare. Each switch is
dioded ROW2COL; staggered key columns (up to 2u wide) share one column bus.

4-layer stackup and what lives where:

- **B.Cu**: sockets/diodes, KEY wires, row-bus stubs, horizontal row buses, LED power
  rails and data-chain rails, USB power feed.
- **In1.Cu**: column ladders - a via at every cathode, a short rung to the cluster bus
  column, and northbound entry lanes into the fanout; each cluster's entry threads to
  its header pad through the corridor between the function and number rows.
- **In2.Cu**: row fanout - each header pad drops south between the pad columns and
  connects through a via to its row bus at the far east end.
- **F.Cu**: LED footprints with a via on every pad; VDD/DOUT hop down to the B.Cu
  rails at the pad rows, DIN/GND likewise.

The header fanout lanes thread the 0.74 mm gaps between the 2.54 mm pad columns
(ROW0/GP0 uses a narrow east lane beside the connector shell). This is tight for
typical fabs: verify against your fabricator's minimum clearance before ordering; the
corridor levels are parameterised at the top of `scripts/generate_kicad.py`.

`firmware/key_matrix.csv` maps every key to its electrical (row, column) and LED chain
index; `config.h` / `keyboard.json` / `rules.mk` are starting points for a QMK/Vial
definition. Full-white current for 117 pixels is far beyond USB capability: the QMK
starting point caps `RGB_MATRIX_MAXIMUM_BRIGHTNESS` at 12/255 and declares 500 mA.
Measure before raising it.

## Important status

This is a **routed prototype, not a manufacturing sign-off**. Schematic ERC is clean
(0/0). PCB DRC is not clean yet: the grid, fanout comb, LED chain and power chain are
placed and the netlist is complete, but a few hundred violations remain, clustered in
fixable families - work through them in this order:

1. LED pad via-in-pad lands vs the chain/power rails on the inner layers (shorting +
   dangling via warnings): re-level the chain hop segments or give the LED pads their
   own attach stubs so no rail crosses a foreign via land on the same layer.
2. Header fanout lanes vs pad/stabilizer-hole clearances - everything is
   parameterised at the top of `scripts/generate_kicad.py` (`COL_FANOUT0`,
   `COL_FANOUT_STEP`, `lane_x`, `ROW_BUS_OFF`).
3. Board-edge clearances (ROW0 east lane, right-margin spines, bottom strip lanes).
4. No ground pours, mounting holes, or case yet.

Then verify the socket/LED geometry against the DXF and your switch cutaways, review
every remaining clearance against your fab rules, and inspect a 1:1 print. Key
apertures and the 16 plate stabilizer slots are reference art on `Dwgs.User` only -
keep them out of Gerbers.

## Regeneration

From the repository root run `python scripts/generate_kicad.py`; it reads the layout
JSON/DXF under `plate-2026-11-07T22_24_25.197Z/` and rewrites the schematic, PCB,
symbols, footprints, and firmware files under `kicad/` (your `Cleaver.kicad_pro` is
preserved).
""")


def main():
    keys, led_order, n_cols = read_keys()
    write_custom_footprints()
    generate_tables_and_symbols()
    generate_board(keys, led_order, n_cols)
    generate_schematic(keys, led_order, n_cols)
    generate_firmware_files(keys, led_order, n_cols)
    write_readme(n_cols)
    print(f"Generated Cleaver: 117 keys, {N_ROWS}x{n_cols} grid, {len(led_order)} RGB LEDs, routed (4L)")


if __name__ == "__main__":
    main()
