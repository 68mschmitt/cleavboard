# Hardware design variants

## Original module-based design

Revision 0.5 remains at the repository's original paths:

- [`../kicad/`](../kicad/): schematic, routed PCB, libraries, firmware, reports.
- [`../mechanical/`](../mechanical/): plate, mounting references, fit models.
- [`../manufacturing/`](../manufacturing/): manufacturing package and review.
- [`../scripts/`](../scripts/): original generators and checks.
- [`../plate-2026-11-07T22_24_25.197Z/`](../plate-2026-11-07T22_24_25.197Z/): original input layout.

These paths are retained because the original generators and mechanical/model
references depend on them, and the existing KiCad project may already be open.
The new design does not replace, regenerate, or relocate these files.

The original source baseline is commit
`8b0f52aa4cf324d2eb17dd09f180e6ee596c49ad`. To compare all original tracked
design files with that baseline, from any working directory run:

```sh
python3 /path/to/cleaver-keyboard/tools/verify_legacy.py
```

The later [Taviana artwork addition](../artwork/taviana/README.md) intentionally
updates both active boards and their artwork-generation support. The historical
baseline comparison will therefore report those changes.

The module-based revision 0.5 additionally updates `kicad/` and its root tools
for bottom-only factory SMT assembly, available HanElectricity sockets and an
SMD bulk capacitor. Its current handoff is [`../manufacturing/rev0.5/`](../manufacturing/rev0.5/);
see the [component review](../kicad/references/COMPONENT-REVIEW.md).

The checker is read-only. It excludes the nested `kicad/.history` Git working
tree, which already had local changes when the new variant was started, and
transient KiCad editor lockfiles, which disappear when an editor closes. It
does not delete or reset those changes. It also excludes the root README,
which is now the navigation page for both designs.

## Embedded RP2040 design

[`embedded-rp2040/`](embedded-rp2040/) is an independent project named
**Cleaver-Embedded**, currently **embedded-0.2**, with underside-only SMD assembly
and cleaned-up routing. See the [before/after review](embedded-rp2040/review/README.md). Open
[`Cleaver-Embedded.kicad_pro`](embedded-rp2040/Cleaver-Embedded.kicad_pro).

Its circuit replaces the module with a directly mounted RP2040, flash, clock,
regulator, USB-C interface, and programming/debug connections. The existing key
layout and matrix are the starting point. Its README records the implemented
features, build/check commands, mechanical implications, and validation status.

Use the generation and verification tools inside that directory for this
variant. The root `scripts/` tools continue to target the original module-based
design. Each variant owns its firmware and manufacturing outputs; a shared
physical key layout does not make their controller connections or fabrication
packages interchangeable.

## Additional variants

Place further hardware variants in their own `designs/<name>/` directory, with
a distinct KiCad project name, local libraries, firmware, and documentation.
Keep output paths within the chosen variant and add a link to the root README.
