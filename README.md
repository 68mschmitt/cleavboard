# Cleaver keyboard

A keyboard for my best tantrum buddy Cleaver: 117 hot-swap MX keys, with RGB and
single-color lighting variants.

## Current revision: 0.11

**[PCB fabrication package](designs/module-rp2040/manufacturing/rev0.11/README.md)** ·
**[Case, switch plate and assembly guide](designs/module-rp2040/mechanical/rev0.11/README.md)**

The PCB screws to the underside of the switch plate, then the combined assembly
slides over tall base posts and screws into the base. A replaceable USB-C bezel
lets the cable opening be fitted after assembling the actual controller.
The case retains its lower 3° profile, hidden cover screws and captured badge.
Use the **rev0.11 PCB, plate, base and cover together**.

## Revision 0.9 showcase (historical)

The earlier **[rev0.9](designs/module-rp2040/manufacturing/rev0.9/README.md)** introduced a
**2 × 1 inch [replaceable illuminated logo](designs/module-rp2040/LOGO.md)** between
the front three-key clusters, with matching rectangular plate/cover openings
and an 8 mm deeper front bezel.

[![Fully assembled Cleaver rev0.9: charcoal case, ivory and grey keycaps, muted red macro keys and a 2 by 1 inch illuminated cyan C badge](designs/module-rp2040/mechanical/rev0.9/case/renderings/Cleaver-rev0.9-assembled.png)](designs/module-rp2040/mechanical/rev0.9/case/renderings/Cleaver-rev0.9-assembled.png)

Rendered from the actual rev0.9 case, populated PCB, switch plate and removable
badge, with all 117 switches, modeled keycaps, stabilizers and mounting hardware.
Colors, keycap profiles and logo illumination are illustrative; the sample “C”
glows cyan while per-key RGB is off.
[Full-resolution render and reproduction details](designs/module-rp2040/mechanical/rev0.9/case/renderings/README.md).

| Feature | Revision 0.9 |
| --- | --- |
| Layout | 117 keys: full-size typing area, numpad, navigation/arrow cluster, left macro column and extra front macro keys |
| Switches | Hot-swap MX, Cherry-compatible **plate-mount stabilizers**, 6.25u spacebar |
| Controller | **Waveshare RP2040-Plus 4MB**, removable via underside SMT sockets; right-facing USB-C |
| Lighting | **117 per-key + 4 logo RGB LEDs**, reverse-mounted; protected USB LED supply |
| Replaceable logo | **50.8 × 25.4 mm badge**, printed light well, 51.2 × 25.8 mm plate/cover openings; QMK/Vial color control |
| Firmware | **QMK / Vial**, with key remapping, macros and RGB control; default and Vial UF2 builds included |
| Enclosure | **5° rear-raised case**, 11 M2 PCB standoffs, controller-socket backstops, removable cover and USB-C opening |
| Dimensions | PCB: **452.44 × 147.64 × 1.6 mm**; case base: approximately **466 × 172 mm** |

### Build and explore

- **Current mechanics:** [rev0.11 cartridge and USB bezel](designs/module-rp2040/mechanical/rev0.11/README.md),
  including STL/STEP, FreeCAD assembly, mounting plan and fit coupons.
- **Electronics:** [design and assembly guide](designs/module-rp2040/README.md),
  [rev0.11 fabrication package, BOM and placement files](designs/module-rp2040/manufacturing/rev0.11/README.md).
- **Earlier mechanics:** [rev0.10 case for the rev0.9 PCB](designs/module-rp2040/mechanical/rev0.10/README.md).
- **Firmware:** [ready-to-flash UF2 files and instructions](designs/module-rp2040/manufacturing/rev0.9/firmware/README.md),
  [firmware source and configuration](designs/module-rp2040/firmware/README.md).
- **Look inside:** [populated PCB previews](designs/module-rp2040/previews/README.md),
  [current mounting plan](designs/module-rp2040/mechanical/rev0.11/case/mounting-plan.svg),
  [recorded validation and remaining prototype checks](designs/module-rp2040/VALIDATION.md).

> **Prototype status:** Electrical/layout checks and firmware builds have recorded
> passing results; physical hardware operation and case fit remain unverified.
> Print the fit coupons first. The case and plate are full-size, unsplit parts;
> the case needs approximately a 466 × 175 mm print area **plus brim clearance**.
> Use the specified long module headers and matching rev0.11 PCB/base/plate/cover. JLCPCB
> engineering/placement approval and physical socket mating remain required.

## Choose a hardware design

| Design | Open in KiCad | Documentation |
| --- | --- | --- |
| **Module RP2040 — rev0.11:** socketed RP2040-Plus, removable PCB/plate cartridge, adjustable USB bezel and illuminated badge | [Cleaver.kicad_pro](designs/module-rp2040/Cleaver.kicad_pro) | [Design and assembly](designs/module-rp2040/README.md), [manufacturing](designs/module-rp2040/manufacturing/README.md) |
| **Embedded RP2040 — embedded-0.2:** onboard RP2040 and USB-C, per-key RGB | [Cleaver-Embedded.kicad_pro](designs/embedded-rp2040/Cleaver-Embedded.kicad_pro) | [Design and status](designs/embedded-rp2040/README.md), [handoff](designs/embedded-rp2040/HANDOFF.md) |
| **Single-color devboard — white-0.1:** YD-RP2040 module, white backlight | [Cleaver-White.kicad_pro](designs/single-color-devboard/Cleaver-White.kicad_pro) | [Design and status](designs/single-color-devboard/README.md), [manufacturing](designs/single-color-devboard/manufacturing/README.md) |

Each design owns its KiCad libraries, firmware, generation tools, validation,
and manufacturing files. Read its documentation for revision and prototype status.

## Repository layout

```text
assets/                        Shared layout inputs and silkscreen artwork
designs/
  module-rp2040/               Original RGB module design, mechanics and releases
  embedded-rp2040/             Integrated-controller RGB design
  single-color-devboard/       Module-based white-backlight design
docs/                          Repository organization and path migration guide
tools/                         Cross-design utilities and repository checks
```

- [Design comparison](designs/README.md)
- [Repository structure and file-placement conventions](docs/REPOSITORY.md)
- [Original keyboard layout](assets/layout/README.md)
- [Taviana artwork, previews and recorded checks](assets/artwork/taviana/README.md)
- [Tools and verification commands](tools/README.md)
