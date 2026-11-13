# Accepted revision 0.9 routing

`Cleaver.ses` contains **all routed copper**, including the power/ground fanouts,
SMD bulk-capacitor, VBUS test pads, **J1/J2 socket escapes and J2.1 VBUS feed**,
and **LED118–LED121 / C218–C221 badge connections**. It carries no placement
instructions; the schematic/shared design is authoritative for placement.
Use the matching revision: rev0.8 has the earlier, clustered badge positions;
the prior rev0.7 archive lacks badge connections,
and rev0.6 targets plated U1 holes instead of the staggered SMT lands. Historical
sessions are retained in `archive/`.

## Restore

Using KiCad 10.0.8's Python environment, from the repository root:

```sh
python3 -B designs/module-rp2040/source/generate_kicad.py --ses designs/module-rp2040/routing/Cleaver.ses
python3 -B designs/module-rp2040/source/check_kicad.py
python3 -B designs/module-rp2040/source/check_routing_roundtrip.py
python3 -B -m unittest discover -s designs/module-rp2040/source -p 'test_*.py'
```

The generator reconstructs schematic-derived nets, model assignments, mounting
holes/keepouts, fiducials, test pads and zones, then imports the complete copper
archive and fills the zones. It does **not** add the former front-side power
fanouts after import. Round-trip validation requires zero ERC/DRC violations,
zero unconnected items and zero schematic/PCB parity issues.

## Provenance

Revision 0.9 spreads the four badge pixels across a 39 mm-wide row, moves their
bypass capacitors and relocates H9 and its rule area to `(263,138)` mm. All
**5,356 pre-badge copper items** retain exact identities, geometry and nets;
the old 161 badge items are replaced by **172** routed items.
`upgrade_rev09_routing.py` records the migration from explicit rev0.8 and rev0.7
backups. See [rev0.9 migration and round-trip evidence](../manufacturing/rev0.9/checks/).

Historical revision 0.8 adds four badge pixels after LED112, with separate bypass capacitors
and off-pad plane access. H9 and its rule area move to `(250,138)` mm. All
**5,356 prior copper items** retain exact identities/geometry/nets; **161** are
added. The result has **4,793 tracks / 724 vias**. `upgrade_rev08_routing.py`
records the migration; `check_rev08_migration.py` checks it independently.
The complete-copper archive round-trips exactly with zero ERC/DRC/parity issues.
See [rev0.8 migration and round-trip evidence](../manufacturing/rev0.8/checks/).

Historical revision 0.7 replaces U1's 40 plated pads with 40 NPTH entries and J1/J2 SMT
lands. `source/upgrade_rev07_routing.py` and `source/finalize_rev07.py` record
the one-time local migration. The accepted board has **4,652 tracks / 704 vias**,
retaining 4,670 original copper identities. A geometric audit confirms copper
outside PCB XY `[398, 0, 452.4375, 29]` mm and all 500 non-controller footprints
are unchanged. Ground socket contacts use separate through-vias; no pin-entry
hole is plated. The complete archive round-trips exactly at its 0.0001 mm
coordinate resolution, and fresh generation passes ERC/DRC/parity. See the
[migration and round-trip reports](../manufacturing/rev0.7/checks/).

Historical revision 0.6 adds two 0.6 mm front-copper segments from Waveshare RP2040-Plus
pin 40 `(449.8975, 22.28)` to the existing TP1 off-pad via `(446, 24.8)`.
All 4,735 prior copper items remained; its total was **4,067 tracks / 670 vias**.
`source/upgrade_rev06_routing.py` records the migration. Header holes and all
carrier GPIO mappings are retained. The complete-copper archive round-trips
exactly through fresh generation.

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
connections use 0.6 mm copper; key power branches use at least 0.4 mm. The badge's
short individual power/ground escapes use 0.3 mm tracks and 0.6/0.3 mm vias.

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
