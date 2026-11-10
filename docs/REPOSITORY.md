# Repository organization

## Where files belong

The repository root is the navigation entry point. Hardware lives under
`designs/<variant>/`; shared creative inputs live under `assets/`; cross-design
utilities live under `tools/`.

Keep each KiCad project, schematic, PCB, library tables, `.pretty` directory and
`.3dshapes` directory together at the design root. This preserves project-relative
`${KIPRJMOD}` references and lets each project open directly in KiCad.

| Content | Location |
| --- | --- |
| Design overview and important engineering notes | Design root Markdown files |
| Generators, routing code, design-specific tests | `designs/<variant>/source/` |
| Firmware sources | `designs/<variant>/firmware/` |
| Full design BOM | `designs/<variant>/manufacturing/BOM.csv` |
| Revision-specific fabrication and assembly handoffs | Design's `manufacturing/` directory |
| Plate, mounting, fit coupons and STL files | Design's `mechanical/` directory |
| Schematic PDF exports | Design's `docs/` directory |
| Datasheets, part reviews and supplied reference photos | Design's `references/` directory |
| ERC/DRC reports, validation and provenance manifests | Design's `validation/` and release directories |
| Board review images and routing comparisons | Design's `review/` or `previews/` directory |
| Original keyboard-layout and plate inputs | `assets/layout/` |
| Shared silkscreen source and artwork previews | `assets/artwork/` |

Revision labels and fabrication filenames retain their original identity.
Read each manufacturing README to select the appropriate package. Bundled model
and footprint licenses remain beside their assets.

## Path migration

| Previous location | Current location |
| --- | --- |
| `kicad/` | `designs/module-rp2040/` |
| `scripts/` | `designs/module-rp2040/source/` |
| `mechanical/` | `designs/module-rp2040/mechanical/` |
| `manufacturing/` | `designs/module-rp2040/manufacturing/` |
| `Cleaver-gerbers.zip` | `designs/module-rp2040/manufacturing/archive/Cleaver-gerbers.zip` |
| `kicad/Cleaver.stl` | `designs/module-rp2040/mechanical/Cleaver.stl` |
| `usb-vbus-ref-pic.jpg` | `designs/module-rp2040/references/usb-vbus-ref-pic.jpg` |
| `artwork/` and `tavi-tac.png` | `assets/artwork/` and `assets/artwork/taviana/tavi-tac.png` |
| `plate-2026-11-07T22_24_25.197Z/` | `assets/layout/` (descriptive filenames) |
| Each project's root `BOM.csv` | Its `manufacturing/BOM.csv` |
| Embedded root ZIP and CPL/JLCPCB CSV exports | `designs/embedded-rp2040/manufacturing/rev0.2/` |
| Embedded and white root schematic PDFs | Each project's `docs/` |

The exact translation is maintained in [`tools/repository_paths.py`](../tools/repository_paths.py).
Commands in the module project's documentation run from the repository root.
Other projects explicitly indicate when to change directories.

### Recorded evidence

Historical reports, build logs, exported netlists and dated manifests may contain
the original paths or machine-specific absolute paths. Those describe the run
that produced the evidence. Use the migration table to locate their inputs;
relocation does not constitute a new electrical check or firmware build.

The module revision 0.5 manufacturing inventory and white-design handoff inventory
are refreshed after path/documentation changes. Older revision 0.4 manufacturing
hashes remain historical evidence and can differ from active revision 0.5 sources.
The module and embedded `validation/manifest.json` files record their dated runs;
their source/documentation hashes remain those snapshots. In particular, the
embedded manifest predates its artwork changes; artwork-era PCB hashes are in
that project's `manufacturing/taviana/manifest.json`.

### Local state

KiCad UI preferences (`*.kicad_prl`), editor locks, backups, Python caches,
virtual environments and nested `.history/` repositories are ignored. Existing
local history and editor files moved with the module project and remain on disk.
They are local working state rather than portable design inputs.
