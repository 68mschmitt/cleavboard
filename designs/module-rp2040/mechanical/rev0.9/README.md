# Rev0.9 — plate for the 2 × 1 inch illuminated logo

Use **`Cleaver-top-plate-rev0.9.stl`** with the rev0.9 PCB and
[matching case, light well and badge](case/README.md).

- **452.4375 × 155.6375 × 1.5 mm** plate: 8 mm deeper at the front than the PCB.
- **51.2 × 25.8 mm** logo opening for the **50.8 × 25.4 mm** visible insert.
- Badge center **(227.6475, 139.1125) mm** in PCB coordinates, centered horizontally
  between M6–M8 and M9–M11 and shifted 1 mm forward from their centerline.
- **H9 at (263,138) mm**; all other mounting and switch positions retained.
- 117 MX openings, seven 2u and one 6.25u Cherry-compatible plate-mount stabilizers.
- Plate underside is 3.5 mm above PCB top; plate top is at 5 mm.

The front web beyond the logo opening is **3.625 mm**. The badge flange rests on
the plate; its rear edge clears the neighboring key-cluster aperture by 0.9375 mm.
Use the supplied 2u/6.25u stabilizer coupons and the
[actual badge fit coupons](case/README.md#badge) to check printed fit.

STL coordinates are millimetres, X right and Y up: PCB `(x,y)` maps to
`(x,155.6375-y)`. To assemble it in the case's PCB-top datum, subtract **8 mm from
STL Y**, then raise Z by **3.5 mm** before applying the case's 5° tilt.
SVG uses PCB top-view coordinates; DXF uses X right and negative PCB Y.

`validation.json` records serialized geometry checks, PCB alignment and hashes.
Regenerate with:

```sh
python3 -B designs/module-rp2040/source/generate_top_plate.py
python3 -B designs/module-rp2040/source/generate_case.py
```
