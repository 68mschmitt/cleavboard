#!/usr/bin/env python3
"""Trace tavi-tac.png into local KiCad footprints; optionally update both PCBs.

Requires KiCad 10 pcbnew, Pillow, Shapely 2 and the potrace executable.
Normal PCB rebuilds use the saved footprints and do not need the tracing tools.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

import pcbnew
from PIL import Image, ImageFilter, ImageOps
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
NAME = "TavianaTactical_34mm"
POSITION = (199, 122)
PROJECTS = [(ROOT / "designs/module-rp2040", "Cleaver"),
            (ROOT / "designs/embedded-rp2040", "Cleaver-Embedded")]


def footprint():
    image = Image.open(ROOT / "assets/artwork/taviana/tavi-tac.png").convert("L")
    ink = image.point(lambda value: 255 if value < 150 else 0)
    ink = ink.crop(ink.getbbox())
    # Preserve the aspect ratio; reinforce fine cables by about 0.05 mm per
    # side so the reduced artwork is more suitable for silkscreen printing.
    ink = ImageOps.expand(ink, 4)
    ink = ink.resize((ink.width * 4, ink.height * 4))
    ink = ink.filter(ImageFilter.MaxFilter(7))
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as directory:
        pbm, geo = Path(directory) / "logo.pbm", Path(directory) / "logo.json"
        ImageOps.invert(ink).convert("1", dither=Image.Dither.NONE).save(pbm)
        subprocess.run(["potrace", "-b", "geojson", "-t", "12", "-O", ".5",
                        "-o", str(geo), str(pbm)], check=True)
        features = json.loads(geo.read_text())["features"]
    points = [p for f in features for ring in f["geometry"]["coordinates"] for p in ring]
    left, right = min(p[0] for p in points), max(p[0] for p in points)
    bottom, top = min(p[1] for p in points), max(p[1] for p in points)
    scale = 34 / (right - left)
    text = [f'(footprint "{NAME}" (version 20241229) (generator "pcbnew")',
            '  (layer "F.Cu")',
            '  (descr "Taviana Tactical logo from tavi-tac.png; 34 mm wide")',
            '  (attr board_only exclude_from_pos_files exclude_from_bom)',
            '  (fp_text reference "LOGO1" (at 0 0) (layer "F.Fab") hide',
            '    (effects (font (size 1 1) (thickness 0.15))))',
            f'  (fp_text value "{NAME}" (at 0 0) (layer "F.Fab") hide',
            '    (effects (font (size 1 1) (thickness 0.15))))']
    for feature in features:
        rings = [[((x - (left + right) / 2) * scale,
                   ((top + bottom) / 2 - y) * scale) for x, y in ring]
                 for ring in feature["geometry"]["coordinates"]]
        polygon = Polygon(rings[0], rings[1:]).simplify(.008, preserve_topology=True)
        assert polygon.is_valid
        poly = pcbnew.SHAPE_POLY_SET()
        outline = poly.NewOutline()
        for index, ring in enumerate([polygon.exterior, *polygon.interiors]):
            hole = -1 if index == 0 else poly.NewHole(outline)
            for x, y in list(ring.coords)[:-1]:
                poly.Append(pcbnew.FromMM(x), pcbnew.FromMM(y), outline, hole)
        # KiCad filled polygons represent holes with zero-width bridges.
        poly.Fracture()
        for index in range(poly.OutlineCount()):
            chain = poly.COutline(index)
            text.append('  (fp_poly (pts')
            for i in range(chain.PointCount()):
                p = chain.CPoint(i)
                text.append(f'    (xy {pcbnew.ToMM(p.x):.6f} {pcbnew.ToMM(p.y):.6f})')
            text.append('  ) (stroke (width 0) (type solid)) (fill solid) (layer "F.SilkS"))')
    return "\n".join([*text, ")", ""])


def apply(folder, project):
    path = folder / f"{project}.kicad_pcb"
    board = pcbnew.LoadBoard(str(path))
    for old in list(board.GetFootprints()):
        if old.GetReference() == "LOGO1":
            if str(old.GetFPID().GetLibItemName()) != NAME:
                raise ValueError(f"{path}: LOGO1 is already in use")
            board.Delete(old)
    logo = pcbnew.FootprintLoad(str(folder / f"{project}.pretty"), NAME)
    logo.SetFPID(pcbnew.LIB_ID(project, NAME))
    logo.SetReference("LOGO1")
    logo.SetPosition(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in POSITION]))
    board.Add(logo)
    logo.SetLocked(True)
    for index, item in enumerate([logo, *logo.GetFields(), *logo.GraphicalItems()]):
        item.SetUuid(pcbnew.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, f"cleaver:tavi:{project}:{index}"))))
    pcbnew.SaveBoard(str(path), board)
    print(f"{path.relative_to(ROOT)}: F.Silkscreen, centre {POSITION} mm, width 34 mm")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="also update the two active boards")
    args = parser.parse_args()
    text = footprint()
    for folder, project in PROJECTS:
        (folder / f"{project}.pretty" / f"{NAME}.kicad_mod").write_text(text)
        if args.apply:
            apply(folder, project)


if __name__ == "__main__":
    main()
