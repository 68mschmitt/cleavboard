# Cleaver component models

Open `../Cleaver.kicad_pcb` in KiCad PCB Editor and press **Alt+3**
(**View → 3D Viewer**). No extra library installation or path configuration is
needed: all assignments use `${KIPRJMOD}/Cleaver.3dshapes/`.

The board includes **597 model placements across 480 component footprints**.
Each switch footprint has both a front-side switch and a back-side socket.
**TP1 is intentionally bare**: it is a wire-soldering pad, not a connector. The
USB tap wire is not modeled because its actual module attachment point and
routing must be established on the purchased module.

Enable **SMD**, **through-hole**, and **unspecified** models in the viewer's
appearance controls. Flip the board with **F** to see the sockets, LEDs, diodes,
and bypass capacitors. If the PCB was already open while its files changed,
reload it from disk after preserving any intentional unsaved edits.

## Coverage and accuracy

| Footprint(s) | Model | Limitations |
| --- | --- | --- |
| SW001–SW117 | KiSwitch Cherry MX plate-mount switch + Kailh MX socket | Representative MX switch, not a statement about the purchased switch's color, housing, or exact dimensions |
| LED001–LED117 | Marbastlib SK6812MINI-E, recentered for reverse mounting | Package/lead geometry; installed height and solder fillets remain approximate |
| D001–D117 | KiCad SOD-123 | Generic package, with cathode band |
| C101–C217 and C1–C3 | KiCad 0805 capacitor | Generic body height/material, not value-specific |
| R1–R4 | KiCad 0805 resistor | Generic package |
| F1 | KiCad 1206 fuse | Representative 3.2 × 1.6 × 0.55 mm PTC body |
| U2 / U3 | KiCad SOT-23-5 / SOT-23-6 | Generic package, not manufacturer marking |
| C5 | Custom 8 mm-diameter, 11.5 mm nominal-body radial capacitor | Simplified EEU-FR1A471 envelope; 3.5 mm pitch; negative stripe faces circular pad 2; not a maximum-tolerance model |
| U1 | **Custom approximate YD-RP2040 assembly** | 53.34 × 22.86 mm PCB, 17.78 mm header spacing, USB-C facing right; see below |

The controller model assumes **direct male headers**: 2.54 mm clearance from the
carrier's top surface to the module PCB's underside, then a 1.6 mm module PCB.
It includes two header strips/pins, a hollow USB-C shell, buttons, representative
ICs, and the onboard LED. Connector details, module thickness, header height,
button/IC locations, and small parts are **visual approximations**, not verified
against the actual board. Optional female sockets are not shown. Changing the
real header/socket stack changes the installed height.

The socket source model already sits below a **1.6 mm carrier**. Do not flip the
entire switch footprint just to move its socket model. The reverse-mount LED
model is likewise normalized for KiCad's normal bottom-side footprint transform;
its emitter faces into the board opening. Its actual leads extend onto the
existing lands without stretching the package to the pad centers.

No keycaps, plate, stabilizers, case, or USB plug/cable model is invented. A 3D
image is **not mechanical clearance sign-off**. Keep the physical checks in
[`../VALIDATION.md`](../VALIDATION.md), especially the actual module, switch/LED
fit, plate/stabilizers, USB plug access, and maximum capacitor height.

## View, reattach, or export

The PCB and local footprint library already have their model assignments.
`scripts/generate_kicad.py` preserves them when regenerating from the accepted
routing archive. To reapply only the model assignments without regenerating
the PCB, run from the repository root:

```sh
python3 -B scripts/add_3d_models.py
python3 -B scripts/add_3d_models.py --check
```

The updater changes only model forms, verifies that all other PCB/footprint
bytes are unchanged, and refuses unfamiliar external model paths. Model-only
updates do not alter the routing archive, pad geometry, or circuit.

Every assigned VRML model has a matching STEP file. For a populated CAD export,
enable **substitute similarly named models** in KiCad's STEP export dialog, or:

```sh
kicad-cli pcb export step --subst-models --output /tmp/opencode/Cleaver-populated.step kicad/Cleaver.kicad_pcb
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

To rebuild the custom models and adapted LED, with FreeCAD's Python modules
available:

```sh
python3 -B scripts/build_3d_models.py
```

Optionally pass `--keyswitch-sources DIRECTORY` containing the two pinned FCStd
sources named in `sources.json` to rebuild the switch/socket STEP exports too.
Normal PCB regeneration is offline and requires **neither FreeCAD nor downloads**.
The source geometry and hashes, not generated STEP timestamps, identify a model
revision. All models are provided without warranty.
