# Sources, attribution and license scope

This project derives its retained keyboard geometry and circuitry from the
Cleaver keyboard repository, revision 0.4, baseline commit
`8b0f52aa4cf324d2eb17dd09f180e6ee596c49ad`.
`source/legacy-base.kicad_pcb` is byte-identical to that commit's
`kicad/Cleaver.kicad_pcb` (SHA-256
`7b83a48035d38c427af6c47ff20fb311b552b90ad182bab0faea532f9db61585`).
`source/legacy-data.json` is the local frozen key/component/mount data used to
preserve revision 0.4. Neither file is a new embedded-controller design output.

The embedded controller circuitry, local symbols, RP2040/0402/button footprints,
generator, completion tools, checks and documentation were developed for this
project on 2026-11-09. The clearance-grid router was adapted from the preceding
Cleaver revision's completion tooling. Firmware derives from the original
Cleaver QMK/Vial target; its existing **GPL-2.0-or-later** notice is retained.
`firmware/LICENSE-GPL-2.0.txt` is the unmodified GPL v2 text from
https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt, retrieved 2026-11-09.

Revision **embedded-0.2** relocates new SMD parts to the underside, introduces
explicit controller courtyards, off-exposed-pad ground vias and hand-laid USB/
clock routing, and replaces the controller/fan-in completion with bend-penalized
octilinear routing and clearance-aware whole-board shortening. The dedicated
USBLC6 and controller 0805 footprints derive from the retained TPS2553/C_0805
land geometry with added courtyards; their copied license notice is retained.
The before-review images/metrics are actual exports of embedded-0.1, captured
before placement/routing changes. Firmware and electrical pin assignments are
unchanged. `source/legacy-base.kicad_pcb` remains the original immutable input.

## Third-party content

- Retained project footprints carry the copied
  [`Cleaver-Embedded.pretty/LICENSE.md`](Cleaver-Embedded.pretty/LICENSE.md),
  **CC BY-SA 4.0**. Retain that notice when redistributing those footprints.
- USB-C, SOT-23-5, SOIC-8W and crystal reference footprints were downloaded from
  `https://github.com/KiCad/kicad-footprints`, paths respectively:
  `Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod`,
  `Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod`,
  `Package_SO.pretty/SOIC-8W_5.3x5.3mm_P1.27mm.kicad_mod`, and
  `Crystal.pretty/Crystal_SMD_3225-4Pin_3.2x2.5mm.kicad_mod`.
  These KiCad libraries use **CC BY-SA 4.0 with the KiCad libraries exception**;
  the full notice is bundled at `Cleaver.3dshapes/licenses/KiCad-LICENSE.md`.
  The downloads used the upstream `master` path rather than recording an
  immutable commit; exact vendored bytes are identified by `references/hashes.json`.
  Active copies remove external 3D-model links; USB-C silk is moved to F.Fab.
- Model authors, pinned upstream commits, conversion details and license texts
  are preserved in `Cleaver.3dshapes/README.md`, `sources.json`, `generated.json`
  and `licenses/`. Historical provenance includes the removed module model;
  it does not imply that model remains part of the embedded design.
- Manufacturer datasheets in `references/` remain copyright their respective
  manufacturers. They are unmodified technical references, not relicensed
  design assets. `references/README.md` identifies manufacturers, documents,
  mirrors, package/pin evidence and inaccessible source URLs.

## No blanket relicensing

The inherited repository does not supply a repository-wide hardware/software
license covering every retained artifact. This handoff preserves available
notices and does **not** infer that a footprint license, firmware license or
model license licenses the complete PCB or all tooling. Obtain the relevant
owner's permission/license for redistribution where no explicit grant exists.
This provenance record is not a new blanket license or a replacement for the
bundled third-party notices.
