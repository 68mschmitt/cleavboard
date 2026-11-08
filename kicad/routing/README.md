# Accepted revision 0.3 routing

`Cleaver.ses` is the **checked, complete routing archive** for the YD-RP2040
module, 8×16 matrix, and corrected reverse-mounted LED footprints. Do not apply
it to another pinout or placement.

## Restore the supplied layout

From the repository root, using KiCad 10.0.8's Python environment:

```sh
python3 -B scripts/generate_kicad.py --ses kicad/routing/Cleaver.ses
python3 -B scripts/check_kicad.py
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

The generator adds the off-pad ground/power fanouts, In1.Cu ground plane,
F.Cu switched-5 V pour, and local bulk-capacitor connection, imports the saved
signal routing/completion copper, and fills the zones. **This round trip was
tested: 0 ERC violations, 0 DRC violations, 0 unconnected items, 0 schematic
parity issues, and 11 passing unit tests.**

## Routing provenance

The accepted base was routed using the actual standalone **Freerouting 1.9.0**
engine, with 0.2 mm signal tracks, automatic neckdown/fanout/optimization disabled,
and only F.Cu/In2.Cu/B.Cu active. The `board_planes` netclass was ignored because
its GND and LED_5V fanouts were already connected through KiCad's filled zones.
Power-input tracks remained 0.6 mm. The final ten connections were completed
using conservative clearance-aware routing (0.2 mm signals, 0.4 mm local power),
then verified in KiCad and incorporated into the archived session.

Freerouting 2.5.0 attempts were **not** accepted. Its `freerouting-router-v19`
setting did not select a bundled classic backend; it fell back to its current
router. Router-reported incompletes also differed substantially from KiCad's
filled-zone connectivity. Do not use those counts as an electrical sign-off.

## Deliberately restart routing

This command **replaces the PCB with an unrouted placement**, so do not use it
merely to inspect or validate the finished board:

```sh
python3 -B scripts/generate_kicad.py --placement-only
```

It exports a new DSN under `/tmp/opencode/cleaver-revision/`. Preparation carries
the 0.5 mm edge rule into routing-only keepouts/boundary margins, explicitly
sets signal/power netclasses, and separates `board_planes` so the router can skip
already-connected pour/fanout nets. KiCad's manufacturing minima are not relaxed.

Any new autorouting result still needs completion and the full checker after
import. Preserve `Cleaver.ses` until a replacement independently passes those
checks. The saved session is what reproduces the supplied copper; repeating an
autorouter run is not guaranteed to produce the same geometry.
