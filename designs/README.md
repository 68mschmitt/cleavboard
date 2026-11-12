# Hardware designs

| Directory | Controller | Lighting | Revision |
| --- | --- | --- | --- |
| [module-rp2040](module-rp2040/README.md) | Top-mounted Waveshare RP2040-Plus | 117 addressable RGB LEDs; VBUS through header pin 40 | 0.6 |
| [embedded-rp2040](embedded-rp2040/README.md) | Onboard RP2040, flash and USB-C | 117 addressable RGB LEDs | embedded-0.2 |
| [single-color-devboard](single-color-devboard/README.md) | Top-mounted YD-RP2040 module | 117 white LEDs; low-current module Vout supply | white-0.1 |

All three retain the 117-key physical layout. Each project's README records its
electrical, mechanical, assembly and prototype status. Use the firmware and
manufacturing package belonging to that design and revision.

## Project structure

Each directory contains its editable KiCad project and project-local symbol,
footprint and 3D-model libraries. Supporting files use these directories:

- `source/`: generators, routing tools and design-specific checks.
- `firmware/`: QMK/Vial source and associated build documentation.
- `manufacturing/`: BOMs, placements, fabrication packages and release records.
- `mechanical/`: plate/case/fit-model files, where supplied.
- `docs/`: exported schematic PDFs, where supplied.
- `references/`: datasheets, sourcing evidence and reference images.
- `validation/`: recorded checks and manifests.
- `routing/`, `review/`, `previews/`: routing archives and visual evidence, where supplied.

The module design reads the shared [layout input](../assets/layout/README.md).
The other variants keep their frozen baseline geometry/data in `source/`.
Project-local libraries and their attribution files travel with their project.

## Historical baseline

The original pre-variant baseline is commit
`8b0f52aa4cf324d2eb17dd09f180e6ee596c49ad`. Run this read-only comparison from
the repository root:

```sh
python3 -B tools/verify_legacy.py
```

The tool maps historical paths to their current locations. Later hardware,
artwork, documentation and tooling changes are expected to differ from that
baseline. Local editor state and the preserved nested `.history` repository
are excluded. See the [path migration guide](../docs/REPOSITORY.md#path-migration).

## Adding a design

Create `designs/<descriptive-name>/` with a distinct KiCad project name and the
supporting directories it needs. Keep generated outputs within that project,
document reproduction commands and status, and add it to this index and the
root README.
