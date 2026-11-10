# Accepted revision 0.5 routing

`Cleaver.ses` contains **all routed copper**, including the power/ground fanouts,
SMD bulk-capacitor and underside wire-pad connections. It carries no placement
instructions; the schematic/shared design is authoritative for placement.
Do not apply older sessions to revision 0.5 placement.

## Restore

Using KiCad 10.0.8's Python environment, from the repository root:

```sh
python3 -B designs/module-rp2040/source/generate_kicad.py --ses designs/module-rp2040/routing/Cleaver.ses
python3 -B designs/module-rp2040/source/check_kicad.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
```

The generator reconstructs schematic-derived nets, model assignments, mounting
holes/keepouts, fiducials, test pads and zones, then imports the complete copper
archive and fills the zones. It does **not** add the former front-side power
fanouts after import. Round-trip validation requires zero ERC/DRC violations,
zero unconnected items and zero schematic/PCB parity issues.

## Provenance

Revision 0.5 retains revision 0.4 copper except for two ROW1 segments next to
the enlarged C5 lands, replaced with a short bottom detour, and five new power
segments / three off-pad vias for C5 and TP1. `designs/module-rp2040/source/upgrade_rev05_routing.py`
records that one-time migration. Socket hole/pad positions and all net mappings
are retained. Normal restoration only needs the current complete session.

Earlier history: revision 0.3's Freerouting 1.9.0 route was the starting point. Revision 0.4
reuses unaffected copper and reroutes connections displaced by underside power
components, mounting-hole keepouts, test pads, fiducials and increased diode/
socket body clearance. Completion used clearance-aware grid routing followed
by KiCad's independent DRC and explicit same-net via/solder-land checks.
Signals use F.Cu/In2.Cu/B.Cu; In1.Cu remains the ground plane. Power-input
connections use 0.6 mm copper; local power branches use at least 0.4 mm.

To archive a newly checked board:

```sh
python3 -B designs/module-rp2040/source/check_kicad.py
python3 -B designs/module-rp2040/source/archive_routing.py designs/module-rp2040/Cleaver.kicad_pcb designs/module-rp2040/routing/Cleaver.ses
```

Always test a fresh generator round trip after updating the archive. The archive
is reproducible copper geometry, not a promise of identical regenerated UUIDs.

## Trace cleanup

`designs/module-rp2040/source/clean_routing.py` simplifies same-width, same-layer runs into straight
and 45-degree sections. It protects pad/via landings and branch junctions, and
checks candidate shortcuts against other copper, holes, LED windows, mounting
envelopes and fiducial mask openings. It requires Shapely >=2 as well as KiCad
Python. To produce a candidate without replacing the accepted PCB:

```sh
python3 -B designs/module-rp2040/source/clean_routing.py designs/module-rp2040/Cleaver.kicad_pcb /tmp/opencode/Cleaver-cleaned.kicad_pcb --report /tmp/opencode/cleanup.json
```

This geometric pass does not prove filled-plane connectivity. Accept changes
only after refilling zones with the project settings and running the full
integration checker. The complete-copper session already includes the accepted
cleanup; normal regeneration does not require rerunning the optimizer.

## Deliberate routing restart

`python3 -B designs/module-rp2040/source/generate_kicad.py --placement-only` **replaces the PCB with
unrouted placement** and exports a routing DSN. It is not a validation command.
The saved complete session is the normal restore path. Any new route needs the
full checker; an autorouter's completion count is not electrical sign-off.
