#!/usr/bin/env python3
"""CC0-1.0 simplified BL-HZ333H-L21-TRE envelope, not vendor/tolerance CAD.

Local +Z is away from solder face; reverse lens in -Z enters PCB.
KiCad transforms bottom footprints; VRML units are 2.54 mm.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def box(center, size, color):
    x, y, z = [v / 2.54 for v in center]
    w, d, h = [v / 2.54 for v in size]
    return f'''Transform {{ translation {x} {y} {z} children [ Shape {{
      appearance Appearance {{ material Material {{ diffuseColor {color} }} }}
      geometry Box {{ size {w} {d} {h} }}
    }} ] }}\n'''


def main():
    text = '#VRML V2.0 utf8\n# CC0-1.0 nominal reverse LED envelope; not vendor CAD\n'
    # Total height 1.1mm is specified; 0.45mm carrier thickness is approximate.
    text += box((0, 0, .225), (3.2, 1.6, .45), '.88 .87 .82')
    text += box((0, 0, -.325), (1.4, 1.6, .65), '.95 .86 .35')
    for x in [-1.4, 1.4]:
        text += box((x, 0, .025), (.4, 1.6, .05), '.7 .7 .73')
    text += box((-1.05, 0, .455), (.12, 1.2, .01), '.1 .65 .1')
    (ROOT / 'Cleaver-White.3dshapes/BL-HZ333H-L21-TRE_Approx.wrl').write_text(text)


if __name__ == '__main__':
    main()
