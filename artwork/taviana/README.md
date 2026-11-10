# Taviana Tactical PCB artwork

Both active PCBs include the supplied [`tavi-tac.png`](../../tavi-tac.png) as
**top silkscreen (F.Silkscreen)**. The locked, board-only `LOGO1` footprint is
excluded from BOM and placement exports. Its text reads normally from above.

## Size and placement

- Nominal width **34 mm**, height **32.48 mm**, original aspect ratio retained.
- Centre **(199, 122) mm**, in KiCad's normal top-view coordinate system.
- Location: open area beside the lower spacebar/thumb-key cluster.
- Fine source strokes reinforced by approximately 0.05 mm per side before
  vector tracing; the white source background is transparent on the board.
- Both projects contain their own editable `TavianaTactical_34mm.kicad_mod`.
  Normal PCB generators load that local footprint automatically.

### Top-view previews

| Module-based | Embedded RP2040 |
| --- | --- |
| [Whole board](module-top.png) | [Whole board](embedded-top.png) |
| ![Module detail](module-detail.png) | ![Embedded detail](embedded-detail.png) |

Previews plot actual KiCad F.Silkscreen, F.Mask and Edge.Cuts in top view.
The colours are preview colours, not an ink/mask colour specification.

## Verification

KiCad **10.0.8**: both boards have **0 DRC violations, 0 unconnected items and
0 schematic-parity issues**. Reports: [module](module-drc.json),
[embedded](embedded-drc.json).

Measured from the final filled artwork polygons, identically on both PCBs:

| Nearest feature | Clearance |
| --- | ---: |
| Top pad / hole bounding box (H9) | 2.91 mm |
| Top component body/courtyard bounding box (SW114) | 1.07 mm |
| 6 mm-diameter mounting-hardware keepout (H9) | 1.01 mm |
| Board edge / LED cutout bounding boxes | 7.12 mm |

The module integration checker passes, including ERC and model assignments;
all seven existing model tests pass. The independent embedded interface checker
passes all 1,363 schematic-to-PCB pin assignments and underside-assembly checks.

## Fabrication files including the logo

- [Module revision 0.4 Gerbers + drills](../../manufacturing/taviana/Cleaver-rev0.4-taviana-fabrication.zip)
- [Embedded revision 0.2 Gerbers + drills](../../designs/embedded-rp2040/manufacturing/taviana/Cleaver-Embedded-0.2-taviana-fabrication.zip)

Each archive has a sibling `manifest.json` recording PCB, artwork-source and ZIP
SHA-256 hashes. These are complete four-layer fabrication exports, using each
board's plot/drill origin. Existing BOM/assembly instructions still apply.
Earlier fabrication archives and recorded PCB hashes predate this artwork;
use the linked Taviana archives for the logo. See each project's documentation
for its prototype status and mechanical requirements.

## Recreate the artwork

With KiCad 10's `pcbnew`, Pillow, Shapely 2 and `potrace` installed:

```sh
python3 tools/add_tavi_artwork.py --apply
```

This traces the supplied image, writes both local library footprints, and updates
`LOGO1` in both active boards. Omit `--apply` to write only the library footprints.
Re-export Gerbers/drills and refresh previews/manifests after changing the artwork.
