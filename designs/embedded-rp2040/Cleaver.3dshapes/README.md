# Cleaver-Embedded component models

Open `../Cleaver-Embedded.kicad_pcb` and use KiCad's 3D Viewer. Model assignments
use `${KIPRJMOD}/Cleaver.3dshapes/`. The retained switch/socket, reverse LED,
diode, capacitor, resistor and LED-power packages have local models. New embedded
controller packages have no bundled models; the old module model is removed.
The view is incomplete and is not mechanical clearance sign-off.

The switch socket is normalized for a 1.6 mm board, and the reverse LED emitter
faces the original opening. The capacitor is a nominal, not worst-case envelope.
Check case/plate, USB connector access, underside components and LED-aperture
tolerances as described in the project README. No keycaps or case are modeled.

## Sources, modifications and licenses

`sources.json` and `generated.json` retain historical source/conversion provenance
from the copied revision 0.4 model set, including records for the removed module.
They are provenance records rather than a current model-placement inventory.
Licenses are bundled in `licenses/`.

- **KiCad community:** 0805, SOD-123, 1206 fuse and SOT-23 models from
  [kicad-packages3D](https://github.com/KiCad/kicad-packages3D), commit
  `b8b3cfdfad88ba66f21002b3de51dc6f7d55ba5a`, **CC-BY-SA-4.0 with the KiCad
  libraries exception**; `licenses/KiCad-LICENSE.md`.
- **KiSwitch / Rafael Silva (perigoso) and keyswitch-kicad-library contributors:**
  switch/socket VRML and FreeCAD source assemblies from
  [kiswitch/kiswitch](https://github.com/kiswitch/kiswitch), commit
  `aefcf65038d48d2666ff14530d482be3c350fa6e`, **MIT**;
  `licenses/KiSwitch-LICENSE-MIT.txt`. STEP conversion preserves assembly geometry.
- **ebastler / marbastlib:** original `LED_SK6812MINI-E.step` from
  [ebastler/marbastlib](https://github.com/ebastler/marbastlib), commit
  `6b0a9a73f579e377816d60b58eac2b3252de7868`, **CERN-OHL-P-2.0**;
  `licenses/Marbastlib-LICENSE.txt`. Modified 2026-11-08: rotated 180° about X,
  translated `(0, -5.08, -1.70)` mm to the solder-side footprint origin, exported
  as `LED_SK6812MINI-E_Reverse.step/.wrl`; VRML body/lead colors added. The original
  STEP remains beside the adapted pair.
- Custom `C_Radial_D8_H11.5_P3.5` model: **CC0-1.0**, to the extent copyright
  applies; `licenses/CC0-1.0.txt`. This dedication does not relicense third-party
  models or the rest of the keyboard design.

Normal project regeneration uses these local files offline. All models are
provided without warranty.
