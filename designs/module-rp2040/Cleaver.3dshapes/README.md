# Cleaver component models

Open `../Cleaver.kicad_pcb` in KiCad PCB Editor and press **Alt+3**
(**View → 3D Viewer**). No extra library installation or path configuration is
needed: all assignments use `${KIPRJMOD}/Cleaver.3dshapes/`.

The rev0.8 board includes **607 model placements across 490 populated/modelled footprints**.
Each switch footprint has both a front-side switch and a back-side socket.
**TP1–TP6, mounting holes and fiducials are intentionally bare**. TP1 is a
VBUS test pad, not a connector. LED power is routed through header pin 40.

Enable **SMD**, **through-hole**, and **unspecified** models in the viewer's
appearance controls. Flip the board with **F** to see the sockets, LEDs, diodes,
and bypass capacitors. If the PCB was already open while its files changed,
reload it from disk after preserving any intentional unsaved edits.

## Coverage and accuracy

| Footprint(s) | Model | Limitations |
| --- | --- | --- |
| SW001–SW117 | KiSwitch MX switch + socket envelope normalized to bottom anchor | Socket envelope approximates HanElectricity CPG151101S11-16; not a supplier-qualified model |
| LED001–LED121 | Marbastlib SK6812MINI-E, recentered for reverse mounting | Last four illuminate the badge; installed height and solder fillets remain approximate |
| D001–D117 | KiCad SOD-123 | Generic package, with cathode band |
| C101–C221 and C1–C3 | KiCad 0805 capacitor | Generic body height/material, not value-specific |
| R1–R4 | KiCad 0805 resistor | Generic package |
| F1 | KiCad 1206 fuse | Representative 3.2 × 1.6 × 0.55 mm PTC body |
| U2 / U3 | KiCad SOT-23-5 / SOT-23-6 | Generic package, not manufacturer marking |
| C5 | Custom Ø10 mm, 10 mm SMD polymer capacitor | Simplified Nichicon PCF1A471MCL1GS; 10.3 mm platform, negative mark toward pad 2; not a tolerance model |
| U1 | **Custom approximate Waveshare RP2040-Plus assembly** | 51 × 21 mm PCB, 17.78 mm header spacing, USB-C facing right; see below |
| J1 / J2 | Custom Harwin M20-7862042 | Nominal 51 × 2.5 mm body, 7.5 mm total height; alternating SMT tails; bottom-entry orientation; not a tolerance model |

The controller model assumes **long male headers into underside female sockets**: 2.54 mm clearance from the
carrier's top surface to the module PCB's underside, then a 1.6 mm module PCB.
It includes two header strips/pins, a hollow USB-C shell, buttons, representative
ICs, and the onboard LED. Connector details, module thickness, header height,
button/IC locations, and small parts are **visual approximations**, not verified
against the actual board. The male posts project **8.13 mm downward**; J1/J2
model the two female sockets below the carrier. U1 is a pad-free board-only
visual reference, not a factory placement. Changing the real header/socket
stack changes the installed height. See the
[interface qualification](../references/CONTROLLER-SOCKETS-0.7.md).

The new CC0-1.0 STEP/VRML pairs and bounds are recorded in `generated-rev07.json`.
Rebuild only these with `source/build_3d_models.py --rev07-only`. Historical
direct-header module models remain available and are not overwritten.

Revision 0.5 uses true bottom-side socket footprints. The legacy mixed-side
switch/socket models were rotated 180° about X and translated Z=−1.6 mm into
their new bottom-anchor coordinate system. KiCad's normal bottom transform now
places the switch above and socket below the **1.6 mm carrier**. The reverse-mount LED
model is likewise normalized for KiCad's normal bottom-side footprint transform;
its emitter faces into the board opening. Its actual leads extend onto the
existing lands without stretching the package to the pad centers.

No keycaps, plate, stabilizers, case, or USB plug/cable model is invented. A 3D
image is **not mechanical clearance sign-off**. Keep the physical checks in
[`../VALIDATION.md`](../VALIDATION.md), especially the actual module, switch/LED
fit, plate/stabilizers, USB plug access, and maximum capacitor height.

## View, reattach, or export

The PCB and local footprint library already have their model assignments.
`designs/module-rp2040/source/generate_kicad.py` preserves them when regenerating from the accepted
routing archive. To reapply only the model assignments without regenerating
the PCB, run from the repository root:

```sh
python3 -B designs/module-rp2040/source/add_3d_models.py
python3 -B designs/module-rp2040/source/add_3d_models.py --check
```

The updater changes only model forms, verifies that all other PCB/footprint
bytes are unchanged, and refuses unfamiliar external model paths. Model-only
updates do not alter the routing archive, pad geometry, or circuit.

Every assigned VRML model has a matching STEP file. For a populated CAD export,
enable **substitute similarly named models** in KiCad's STEP export dialog, or:

```sh
kicad-cli pcb export step --subst-models --output /tmp/opencode/Cleaver-populated.step designs/module-rp2040/Cleaver.kicad_pcb
```

The original KiSwitch VRML files preserve their source colors. Their STEP
counterparts are exported from the corresponding source FreeCAD assemblies.
Generated STEP counterparts are geometry-oriented; colors may differ from the
VRML viewer. Top/bottom raytraced previews are in [`../previews/`](../previews/).

## Sources, modifications, and licenses

[`sources.json`](sources.json) records pinned source URLs, original hashes,
conversion inputs, and modifications. Licenses are bundled in `licenses/`.

- **KiCad community:** unmodified 0805, SOD-123, 1206 fuse, and SOT-23 models from
  [kicad-packages3D](https://github.com/KiCad/kicad-packages3D), commit
  `b8b3cfdfad88ba66f21002b3de51dc6f7d55ba5a`. **CC-BY-SA-4.0 with the KiCad
  libraries exception**; see `licenses/KiCad-LICENSE.md`.
- **KiSwitch / Rafael Silva (perigoso) and keyswitch-kicad-library contributors:**
  original switch/socket VRML and FreeCAD source assemblies from
  [kiswitch/kiswitch](https://github.com/kiswitch/kiswitch), commit
  `aefcf65038d48d2666ff14530d482be3c350fa6e`. Used under **MIT**;
  see `licenses/KiSwitch-LICENSE-MIT.txt`. STEP conversion does not change the
  assembly geometry. The source FCStd files can be fetched from `sources.json`;
  they are not required for viewing the board.
- **ebastler / marbastlib:** original `LED_SK6812MINI-E.step` from
  [ebastler/marbastlib](https://github.com/ebastler/marbastlib), commit
  `6b0a9a73f579e377816d60b58eac2b3252de7868`. **CERN-OHL-P-2.0**;
  see `licenses/Marbastlib-LICENSE.txt`. Modified **2026-11-08**: rotated 180°
  about X, translated `(0, -5.08, -1.70)` mm to a solder-side footprint origin,
  and exported as `LED_SK6812MINI-E_Reverse.step/.wrl`; VRML body/lead colors
  added. The untouched source STEP is retained alongside the adapted pair.
- The original custom `YD_RP2040_Approx` and `C_Radial_D8_H11.5_P3.5` models are
  dedicated to the public domain under **CC0-1.0**, to the extent copyright
  applies; see `licenses/CC0-1.0.txt`. This dedication does not relicense any
  third-party model or the rest of the keyboard design.
- Revision 0.5 `C_PCF_D10_H10` is also **CC0-1.0**. The two `BottomAnchor` /
  `HanElectricity_Approx` models are transformations of the MIT KiSwitch STEP
  sources above; VRML wraps the original meshes and preserves their colors.
  `generated-rev05.json` records
  their envelopes. Rebuild these additions using
  `python3 -B designs/module-rp2040/source/build_3d_models.py --rev05-only`.
- Revision 0.6 `Waveshare_RP2040_Plus_Approx` is **CC0-1.0**. Its nominal PCB and
  header geometry follows the [Waveshare drawing](../references/RP2040-Plus-dimensions.webp).
  USB-C projection/height, battery connector, buttons, and IC bodies are visual
  approximations. `generated-rp2040-plus.json` records its envelope. Rebuild with
  `python3 -B designs/module-rp2040/source/build_3d_models.py --waveshare-only`.

To rebuild the custom models and adapted LED, with FreeCAD's Python modules
available:

```sh
python3 -B designs/module-rp2040/source/build_3d_models.py
```

Optionally pass `--keyswitch-sources DIRECTORY` containing the two pinned FCStd
sources named in `sources.json` to rebuild the switch/socket STEP exports too.
Normal PCB regeneration is offline and requires **neither FreeCAD nor downloads**.
The source geometry and hashes, not generated STEP timestamps, identify a model
revision. All models are provided without warranty.
