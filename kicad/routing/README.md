# Accepted revision 0.4 routing

`Cleaver.ses` contains **all routed copper**, including the power/ground fanouts,
bulk-capacitor connection and underside rerouting. It carries no placement
instructions; the schematic/shared design is authoritative for placement.
Do not apply revision 0.3 sessions to revision 0.4 placement.

## Restore

Using KiCad 10.0.8's Python environment, from the repository root:

```sh
python3 -B scripts/generate_kicad.py --ses kicad/routing/Cleaver.ses
python3 -B scripts/check_kicad.py
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

The generator reconstructs schematic-derived nets, model assignments, mounting
holes/keepouts, fiducials, test pads and zones, then imports the complete copper
archive and fills the zones. It does **not** add the former front-side power
fanouts after import. Round-trip validation requires zero ERC/DRC violations,
zero unconnected items and zero schematic/PCB parity issues.

## Provenance

Revision 0.3's Freerouting 1.9.0 route was the starting point. Revision 0.4
reuses unaffected copper and reroutes connections displaced by underside power
components, mounting-hole keepouts, test pads, fiducials and increased diode/
socket body clearance. Completion used clearance-aware grid routing followed
by KiCad's independent DRC and explicit same-net via/solder-land checks.
Signals use F.Cu/In2.Cu/B.Cu; In1.Cu remains the ground plane. Power-input
connections use 0.6 mm copper; local power branches use at least 0.4 mm.

To archive a newly checked board:

```sh
python3 -B scripts/check_kicad.py
python3 -B scripts/archive_routing.py kicad/Cleaver.kicad_pcb kicad/routing/Cleaver.ses
```

Always test a fresh generator round trip after updating the archive. The archive
is reproducible copper geometry, not a promise of identical regenerated UUIDs.

## Deliberate routing restart

`python3 -B scripts/generate_kicad.py --placement-only` **replaces the PCB with
unrouted placement** and exports a routing DSN. It is not a validation command.
The saved complete session is the normal restore path. Any new route needs the
full checker; an autorouter's completion count is not electrical sign-off.
