# Cleaver keyboard

A keyboard for my best tantrum buddy Cleaver: 117 hot-swap MX keys with per-key RGB.

## Choose a hardware design

| Design | Open in KiCad | Documentation |
| --- | --- | --- |
| **Module-based, revision 0.5** — top YD-RP2040, all factory components bottom SMD | [`kicad/Cleaver.kicad_pro`](kicad/Cleaver.kicad_pro) | [Design and assembly](kicad/README.md), [recorded validation](kicad/VALIDATION.md), [live sourcing review](kicad/references/COMPONENT-REVIEW.md) |
| **Embedded RP2040, revision 0.2** — onboard processor/USB-C, underside SMD assembly | [`designs/embedded-rp2040/Cleaver-Embedded.kicad_pro`](designs/embedded-rp2040/Cleaver-Embedded.kicad_pro) | [Project documentation and status](designs/embedded-rp2040/README.md), [routing before/after](designs/embedded-rp2040/review/README.md) |

The original module-based design keeps its existing paths and files. The embedded
design is a separate KiCad project with its own libraries, firmware, generation
tools, and validation results. Check each project's documentation for its actual
completion and prototype status.

Both PCBs now include **Taviana Tactical top-side silkscreen artwork**.
See [placement previews, checks and updated fabrication ZIPs](artwork/taviana/README.md).

## Repository layout

```text
kicad/                         Original module-based electronics and firmware
mechanical/                    Original revision 0.4 plate/case references
manufacturing/rev0.5/          Current module-based manufacturing package
scripts/                      Original design's generation/verification tools
plate-2026-11-07T22_24_25.197Z/ Original layout input
designs/embedded-rp2040/       New integrated-controller design
tools/                        Repository-level utilities
```

The root `Cleaver-gerbers.zip` and loose Gerbers in `kicad/` are historical
exports. The original design's revision-specific handoff is in
[`manufacturing/rev0.5/`](manufacturing/rev0.5/), with its
[component review](kicad/references/COMPONENT-REVIEW.md). Manufacturing and mechanical
artifacts are design-specific; use the embedded project's own instructions for
that board.

See [`designs/README.md`](designs/README.md) for project boundaries and comparison
with the historical original-design baseline.
