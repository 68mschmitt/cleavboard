# Cleaver KiCad project

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
7 x 17 grid needs; Pro Micro-style footprints do not.

## Matrix and routing

Typical custom-QMK physical grid: **7 row wires** (the seven key rows, GP0-GP6)
x **17 column wires** (GP7-GP22, GP26), RGB data GP27, GP28 spare. Each switch is
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
