# Actual PCB routing review — embedded-0.1 → embedded-0.2

These are **KiCad exports of the actual boards**, rasterized with librsvg. All
views use the same unmirrored board coordinates. Zone fills are hidden only in a
temporary plotting copy so tracks remain visible; the validated PCB has filled
zones. The controller's SMD assembly moves from front to bottom.

## Images

| View | Before | After |
| --- | --- | --- |
| Controller assembly-side copper | [F.Cu](before/F.Cu-controller.png) | [B.Cu](after/B.Cu-controller.png) |
| Bottom body/courtyard overlay | [Before](before/B.Assembly-controller.png) | [After](after/B.Assembly-controller.png) |
| Whole-board bottom copper | [Before](before/B.Cu.png) | [After](after/B.Cu.png) |
| Whole-board front copper | [Before](before/F.Cu.png) | [After](after/F.Cu.png) |
| Upper-right bottom fan-in | [Before](before/B.Cu-fan-in.png) | [After](after/B.Cu-fan-in.png) |
| Upper-right front fan-in | [Before](before/F.Cu-fan-in.png) | [After](after/F.Cu-fan-in.png) |
| Inner-1 fan-in | [Before](before/In1.Cu-fan-in.png) | [After](after/In1.Cu-fan-in.png) |
| Inner-2 fan-in | [Before](before/In2.Cu-fan-in.png) | [After](after/In2.Cu-fan-in.png) |

Matching `.svg` files beside every PNG retain vector detail. Full-board and
controller/fan-in crops are supplied for all four copper layers.

## Measured routing changes

| Whole-board metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Track segments | 9,693 | 4,556 | −53.0% |
| Degree-two bends | 8,111 | 2,984 | −63.2% |
| Segments shorter than 0.2 mm | 4,906 | 508 | −89.6% |
| Vias | 874 | 826 | −48 |
| Non-45° segments, 1 µm tolerance | 217 | 203 | −14 |
| Total track length | 20,197.980 mm | 20,324.962 mm | **+0.63%** |

The visual improvement is chiefly removal of staircase routing, regular MCU
escapes and longer straight/45° fan-in sections. Repeated key cells remain
recognizable. Whole-board shortening also reduces jogs outside the controller:
the endpoint-classified outside region has 4,054 → 3,939 segments and
2,744 → 2,628 bends. That classification includes boundary-crossing tracks in
full, so it is a diagnostic region count, not a clipped geometric measurement.

**Overall copper length increases by 126.982 mm.** Moving the MCU farther right
and fitting all bodies/decouplers on one side lengthens some matrix/debug paths.
USB, XIN and core-supply routing become materially shorter; total-length
reduction is not claimed. Remaining arbitrary-angle segments are predominantly
inherited keyboard pad landings. These metrics and images make the achieved
improvement and remaining tradeoffs reviewable independently of DRC.

| Local net(s) | Segments before → after | Vias before → after | Length before → after |
| --- | ---: | ---: | ---: |
| USB, all four nets | 132 → 37 | 9 → **0** | 54.172 → **34.857 mm** |
| XIN | 166 → **5** | 2 → **0** | 12.297 → **5.659 mm** |
| XOUT | 16 → 4 | 0 → 0 | 3.213 → 3.804 mm |
| XTAL_OUT | 48 → 4 | 2 → **0** | 6.384 → 5.481 mm |
| Six QSPI nets | 316 → **40** | 10 → **6** | 79.224 → 81.487 mm |
| 1V1 | 247 → **30** | 10 → **6** | 57.453 → **38.567 mm** |
| 3V3 | 356 → **85** | 19 → **12** | 109.304 → **92.474 mm** |

USB and clock signal copper stays entirely on B.Cu. In2 ground-reference
corridors are reserved beneath it. Every controller capacitor ground pad and
both crystal ground pads have a nearby ground via within 1.5 mm, connected by
local bottom copper; the final maximum measured distance is 1.4142 mm.
Four ordinary 0.5/0.3 mm ground vias sit outside the QFN exposed pad and paste.
An additional 36 roomy routing vias were promoted from 0.4/0.2 to 0.5/0.3 mm
after clearance validation.

## Evidence and reproduction

- [Before metrics](before/metrics.json), [after metrics](after/metrics.json):
  whole-board, per-layer, per-net and outside-controller geometry, with PCB hashes.
- [Independent-tool comparison](../validation/routing-comparison.json): generated
  using the parent's read-only `tools/inspect_routing.py`.
- [Final electrical/assembly checks](../validation/validation.json),
  [ground-return audit](../validation/local-ground.json),
  [ordinary-via promotion](../validation/ordinary-vias.json),
  [exact archive round trip](../validation/roundtrip.json).

```sh
python3 -B source/review.py /path/to/before.kicad_pcb before
python3 -B source/review.py Cleaver-Embedded.kicad_pcb after
```

The before snapshot used here is
`/tmp/opencode/cleaver-embedded-bottom-before/Cleaver-Embedded.kicad_pcb`.
The final schematic, pads, holes, outline and copper remain editable in KiCad.
