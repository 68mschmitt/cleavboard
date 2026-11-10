# Cleaver White — top YD-RP2040, bottom-only SMT

**New isolated, editable prototype design; revision `white-0.1`.** Open
[`Cleaver-White.kicad_pro`](Cleaver-White.kicad_pro) in KiCad 10. The original
117-key positions, ROW2COL matrix, hot-swap sockets, outer outline, 11 mounts and
top controller/header position are retained.

The 117 addressable LEDs are replaced by **BrtLed BL-HZ333H-L21-TRE reverse-mount
white LEDs (C5123487)**, each with a **3.9 kΩ 1% resistor**. All 117 hot-swap
sockets are **HanElectricity CPG151101S11-16 (C41430893)**. Exact identities and
catalog codes are embedded in both KiCad schematic and PCB fields; switch key
legends are retained in the `Key` field. An AO3400A switches the LEDs' common
return with GP27 PWM. A TPS2553, enabled by GP28, limits the whole lighting branch
to **50/75/100 mA minimum/typical/maximum** using its documented ILIM-to-IN mode.

**No power wire or through-hole capacitor is used.** Pin 40 supplies the small
protected lighting load through the ordinary module header. This is a deliberate
low-current use of its BAT54C-protected Vout, **not a raw USB VBUS connection**.
Read [POWER.md](POWER.md): the module's own current and diode temperature must be
qualified on the actual purchased revision. The available module schematic is
V1.1; the supplied listing is V1.3. Full-current RGB and 1 mA × 117 lighting cannot
be substituted into this design.

## Deliverables

### Populated 3D view

Open `Cleaver-White.kicad_pcb` in PCB Editor and press **Alt+3**; press **F**
to see the underside. Models are bundled and already assigned. Enable SMD,
through-hole and unspecified models in the viewer. Reload the PCB if it was
already open when the models were added.

See [top preview](review/3d-top.png), [bottom preview](review/3d-bottom.png),
and [model details/approximations](Cleaver-White.3dshapes/README.md).

The top silkscreen includes the same **34 mm Taviana Tactical artwork**, centred
at **(199, 122) mm**, as the other Cleaver projects. `LOGO1` is locked and excluded
from the BOM and placement files. The local footprint and generator retain it.

| Item | Location |
|---|---|
| Editable project, schematic, routed 4-layer board | `Cleaver-White.kicad_*` |
| Self-contained symbols/footprints | `Cleaver-White.kicad_sym`, `Cleaver-White.pretty/`, local library tables |
| Real KiCad schematic PDF | [Full sheet](docs/Cleaver-White-schematic.pdf), [four readable detail pages](docs/Cleaver-White-schematic-details.pdf) |
| Actual copper, including filled zones | [Bottom](review/bottom-copper.png), [top](review/top-copper.png), [controller detail](review/controller-bottom-detail.png), [key-cell detail](review/key-cells-bottom-detail.png) |
| All-layer vector review | `review/*.svg` / `review/*.png` |
| Exact purchasing BOM | [BOM.csv](manufacturing/BOM.csv), [sourcing evidence](references/SOURCES.md) |
| 476 bottom factory placements | `manufacturing/BOM-JLCPCB.csv`, `manufacturing/CPL-JLCPCB.csv` |
| Gerbers/drills and prototype ZIP | `manufacturing/fabrication/`, `manufacturing/Cleaver-White-white-0.1-prototype.zip` |
| Fresh ERC/DRC, parity, geometry assertions | [validation/validation.json](validation/validation.json) |
| Monochrome QMK/Vial source, UF2s, build logs | [firmware/](firmware/README.md) |
| Repeatable generation and export | `source/` |

All **476 factory-fitted parts** are underside SMD: 117 sockets, 117 matrix
diodes, 117 LEDs, 117 branch resistors and eight support components. Only the
40 module-header electrical pins require owner through-hole soldering. The MX
switches snap into the plate and sockets. Test pads and fiducials are bare lands.

The white LED is a real reverse-mount part, with its own two-pin footprint and
**2.1 × 2.3 mm optical apertures**. These are not the old MINI-E openings. Its
short ceramic carrier requires a narrow, explicitly scoped land-to-aperture
clearance; see [MECHANICAL.md](MECHANICAL.md). Factory confirmation of these
small apertures/lands and reverse-LED placement is required. Both replacement
parts have populated JLCPCB catalog codes in the BOM. See the
[live LED sourcing record](references/LED-SOURCING-2026-11-10.md).

## Validation status

KiCad **10.0.8**: **0 ERC, 0 DRC, 0 unconnected, 0 schematic-parity issues** after
zone refill and complete-routing regeneration. Independent assertions check all
117 matrix/LED circuits, exact legacy mechanical geometry, bottom component
bodies and mounting envelopes, off-pad vias, no front paste, and the header-only
through-hole condition. Five inherited non-electrical ignored categories are
listed in the JSON; no new ignored category or DRC exclusion was added. There
is one documented custom rule for the reverse-LED solder lands.

The [replacement checks](validation/replacements.json) cover all 117 new sockets
and LEDs, including exact identities, socket hole/land coordinates, LED cathode
orientation, maximum lens fit in a minimum rounded aperture, expanded body
envelopes and resistor-current bounds. Calculated minimum lens clearance is
**0.110 mm** and nearest checked body gap is **0.42 mm**, conditional on the
specified fabrication/placement tolerances. These are CAD checks, not a reflow
or brightness test.

Routing round-trip comparison retains all **3,384 tracks/vias**. Independent
export checks pass for **476 placements, 117 socket centroids and 957 SMD pad
references**, plus fabrication ZIP contents and firmware source/binary hashes.

This is **not fabrication-qualified**. Unresolved physical checks: actual module
revision/diode identification, module baseline/USB-suspend current and diode
temperature; LED fit, polarity, reflow/pickup and low-current brightness; case,
plate and socket samples; USB enumeration, matrix rollover and PWM rail behavior.
These are explicit prototype gates, not claims of tests already performed.

## Rebuild/check/export

Use Python with KiCad's `pcbnew` module and these dependencies:

```sh
python3 -m venv --system-site-packages /tmp/opencode/cleaver-white-tools
/tmp/opencode/cleaver-white-tools/bin/pip install shapely pillow pypdf cairosvg
PY=/tmp/opencode/cleaver-white-tools/bin/python
$PY -B designs/single-color-devboard/source/generate.py
$PY -B designs/single-color-devboard/source/check.py
$PY -B designs/single-color-devboard/source/export.py
$PY -B designs/single-color-devboard/source/check_exports.py
$PY -B designs/single-color-devboard/source/manifest.py
```

The normal generator restores `source/complete.ses` and refills zones. It reads
only files inside this project. `source/layout.json` freezes the original matrix
and coordinates; `source/base-rev04.kicad_pcb` freezes original geometry/matrix
copper. Generation inputs and outputs stay within this design.

`generate.py --placement` **resets the board's new routing** and is only for a
deliberate routing restart. `fanout.py`, `route.py`, and `grid_route.cpp` record
the completion tools; `archive_routing.py` archives subsequently checked copper.
They are unnecessary for normal restoration. See [PROVENANCE.md](PROVENANCE.md).

## Mechanical compatibility

Board: **452.4375 × 147.6375 mm**, nominal **1.6 mm**, four copper layers. Use the
original carrier's plate-mount stabilizers and mounts. The original controller
notch is retained. The former top capacitor opening may remain unused or be
closed in a revised plate; no new plate opening is required. Allow at least
**3 mm free space below the PCB** for sockets, solder and header tails; support
parts fit inside that envelope. Detailed aperture/assembly constraints are in
[MECHANICAL.md](MECHANICAL.md) and [manufacturing/README.md](manufacturing/README.md).
