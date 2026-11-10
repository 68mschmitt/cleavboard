# Complete copper archive — embedded-0.2

`Cleaver-Embedded.ses` is the complete copper geometry, including retained
keyboard routing, new controller routes, QFN fanout and ground stitching. It
has no placement instructions. `via-options.json` preserves via tenting, which
the Specctra format does not encode. The generator owns placement and pad nets.

After editing and successfully checking the board:

```sh
python3 -B source/check.py
python3 -B source/archive.py
python3 -B source/generate.py --route routing/Cleaver-Embedded.ses
python3 -B source/check.py
```

The round trip is essential: an archive is not proof of valid connectivity.
Save a copy of the completed board before regenerating and run
`python3 -B source/compare_roundtrip.py /path/to/completed-backup.kicad_pcb`.
It compares the copper multiset, via dimensions/tenting, footprint/pad geometry,
pad nets and outline independently of generated UUIDs. Follow with `source/check.py`.
Coordinates use `resolution um 1000` (1 nm) to preserve the source geometry.
Do not import the original module project's routing session into this project.

`source/route.py` and `grid_route.cpp` were adapted from the previous revision's
clearance-grid completion tools. The backend can be built with:

```sh
mkdir -p /tmp/opencode/cleaver-embedded
g++ -O3 -std=c++17 source/grid_route.cpp -o /tmp/opencode/cleaver-embedded/grid-route
```

The router uses a 25 µm grid (optional `--step .01`) and bend/via penalties,
considering actual pads, holes, mounting keepouts and tracks. In1.Cu signal
escapes are restricted to x=399..444, y<25.5 mm. Adjacent In2 ground corridors
are reserved beneath the bottom USB/clock paths in `source/critical.py`.
The final archive also includes controlled corner escapes, local rerouting and
whole-board shortening using `source/smooth.py`. Smoothing preserves electrical
terminals and rejects obstacle crossings; independent zone refill and KiCad DRC
remain authoritative, particularly where changing a trace can split a pour.

Development `escape.py`, `dogleg.py`, `adjust.py`, `stitch.py`, `clock_bridge.py`
and `annotate.py` describe **historical embedded-0.1 top-side placement**. They
are not part of normal regeneration and must not be applied to this bottom-side
layout. The completed archive is the reproducible routing source. The optional
`--placement` command deliberately resets routing and writes a development
`placement.dsn`; it is not a substitute for importing the completed archive.

`source/prune.py` checks each dead-end removal with a fresh DRC and rolls back
any edit that disconnects a live junction. When a track has a live mid-span
connection, it trims the unused end instead. This matters for retained tracks
cut at the old controller boundary.

`source/local_ground.py` provides short bottom-pad returns through adjacent
ground planes and validates removal of redundant long ground runs. The completed
board includes dedicated local returns for every controller capacitor and both
crystal ground pads; `source/check.py` records final via distances.
`source/ordinary_vias.py` promotes roomy 0.40/0.20 mm vias to 0.50/0.30 mm,
rolling back each conflicting candidate after full KiCad DRC. These development
passes are already captured in the complete archive and need not be rerun during
normal regeneration.
