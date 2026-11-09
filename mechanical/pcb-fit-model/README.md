# Four-piece PCB size / shape mockup

Print **one of each**, separately, on the **235 × 235 mm** bed. Assemble them in
number order from left to right:

- [1 — left](Cleaver-PCB-1-left.stl): **127.00 × 147.64 mm**
- [2 — middle-left](Cleaver-PCB-2-middle-left.stl): **128.30 × 147.64 mm**
- [3 — middle-right](Cleaver-PCB-3-middle-right.stl): **122.96 × 147.64 mm**
- [4 — right](Cleaver-PCB-4-right.stl): **126.86 × 147.64 mm**

Each section is under **129 × 148 mm**, leaving ample room for a 5 mm brim.

Assembled dimensions: **452.4375 × 147.6375 × 1.6 mm**, matching the saved PCB.
[assembly-preview.svg](assembly-preview.svg) shows the joint and hole layout from
above: blue, orange, green and purple are sections 1–4. Numbers in the preview
are annotations, not raised features on the printed PCB.

## Printing and joining

- Import in **millimetres**, **100% scale**. Print one section per build plate.
- All four files already lie flat, underside on the bed at Z=0. No supports needed.
- Suggested starting settings: PLA, 0.4 mm nozzle, 0.2 mm layers, 3 walls and
  solid infill. The 1.6 mm sheet is eight 0.2 mm layers.
- Use a 5 mm **outer-only brim** if needed to keep the long edges flat. Remove
  it and clean any first-layer lip around the joint before fitting the pieces.
- Each joint has two opposed round-headed puzzle tabs and matching recesses.
  Keep the sections flat and **lower one into the other from above**, like a
  jigsaw puzzle. The undercut heads prevent sliding the sections straight
  together sideways.
- The mating edges have **0.20 mm total XY clearance**. This is a locating joint,
  not a guaranteed snap fit; support all four sections when lifting the thin model.
  A small piece of removable tape underneath can hold the mockup during handling.
- Printer hole shrinkage and elephant's foot can affect fit. Keep overall scale
  at 100%; use local slicer compensation or trim the joint rather than scaling
  the board, which would change switch and mounting-hole spacing.

## What the model includes

The geometry is read directly from `kicad/Cleaver.kicad_pcb`:

- The actual outer Edge.Cuts shape and **1.6 mm PCB thickness**.
- All **117 LED windows**, **596 NPTH holes** (switches/sockets and 11 mounts),
  and **43 plated component holes** (controller headers, capacitor, USB tap).
- Three seams routed between holes, each with two interlocking tabs in clear
  areas. **All 756 existing openings remain whole on individual sections.**

Electrical copper, soldermask and component bodies are omitted. The **667 tiny
electrical via holes** are also omitted because they are not mechanical fit
features. Component drill sizes are nominal fabrication dimensions; this print
checks the board's physical layout rather than plated-hole manufacturing fit.

The underside sockets, MCU and capacitor heights are not represented. This is
a bare-PCB mockup for size, hole positions, and case/plate alignment.

## Coordinates and checks

Each STL has its own lower-left origin for convenient printing. To align them
in CAD, apply the `assembled_translation_mm` in `validation.json`; no rotation
or scaling is needed. Z=0 is the bottom of the printed PCB; Z=1.6 is its top.

The generator checks that all four planar sections are connected, the joints don't
cut any existing openings, the full outline dimensions are retained, and the
parts fit the print bed with a 5 mm brim allowance. It reloads the exported STLs
and checks watertightness, winding, volume, opening topology and dimensions.
Results and the source-board SHA-256 are in [validation.json](validation.json).

## Regeneration

Use Python with KiCad 10's `pcbnew`, Shapely >=2.1, numpy and trimesh:

```sh
python3 -B scripts/generate_pcb_fit_model.py
```

The mating clearance can be adjusted with `--gap` in millimetres. The generator
always uses the saved PCB; save PCB edits before regenerating. Its seam is specific
to this layout and will reject a changed outline or a hole too close to the joint.
