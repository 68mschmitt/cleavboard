"""Raised, font-independent fit-set IDs on external coupon tabs (millimetres)."""
from generate_case import freecad

# name: (ID, tab side, tab bottom, thickness, emboss toward -Z)
# Base parts are already desk-flat; the other parts retain their PCB frame.
LABELS = {
    'Cartridge-stack-coupon-base': ('A1', -1, None, 1.5, False),
    'Cartridge-stack-coupon-plate': ('A2', 1, 3.5, 1.5, True),
    'Cartridge-stack-coupon-dummy-PCB': ('A3', -1, -1.6, 1.6, False),
    'USB-bezel-fit-coupon-base': ('B1', -1, None, 1.5, False),
    'USB-bezel-fit-coupon-cover': ('B2', -1, 9.3, 1.5, True),
    'USB-bezel-blank': ('B3', 1, -2, 1.5, False),
    'Front-fastener-fit-coupon-base': ('C1', -1, None, 1.5, False),
    'Front-fastener-fit-coupon-cover': ('C2', 1, 9.3, 1.5, True),
    'Logo-fit-coupon-cover': ('D1', 1, 9.3, 1.5, True),
    'Logo-fit-coupon-plate-with-height-gauges': ('D2', -1, 3.5, 1.5, False),
    'Logo-gasket-cutting-pattern-0.8mm': ('D3', -1, 0, .8, False),
    'Stabilizer-fit-coupon-2u': ('E1', -1, 0, 1.5, False),
    'Stabilizer-fit-coupon-6.25u': ('F1', -1, 0, 1.5, False),
    'Controller-insertion-support-jig': ('G1', -1, 0, 2, False),
}

GLYPHS = {
    'A': ('010', '101', '111', '101', '101'),
    'B': ('110', '101', '110', '101', '110'),
    'C': ('111', '100', '100', '100', '111'),
    'D': ('110', '101', '101', '101', '110'),
    'E': ('111', '100', '110', '100', '111'),
    'F': ('111', '100', '110', '100', '100'),
    'G': ('111', '100', '101', '101', '111'),
    '1': ('010', '110', '010', '010', '111'),
    '2': ('110', '001', '010', '100', '111'),
    '3': ('110', '001', '010', '001', '110'),
}


def label_coupon(name, original):
    """Attach an outboard tab without changing any original mating surface.

    Only the 1 mm anchor overlaps the original bounding box; the raised text
    lies entirely outside it. Embossing faces away from the print bed.
    """
    app, part = freecad()
    code, side, z, thickness, underside = LABELS[name]
    bounds = original.BoundBox
    z = bounds.ZMin if z is None else z
    edge = bounds.XMin if side < 0 else bounds.XMax
    x = edge-12 if side < 0 else edge-1
    # Pick a connected solid edge, avoiding cutouts and rounded corners.
    candidates = [bounds.YMin+1+(bounds.YLength-9)*i/20 for i in range(21)]
    tabs = [part.makeBox(13, 7, thickness, app.Vector(x, y, z)) for y in candidates]
    contacts = [original.common(tab).Volume for tab in tabs]
    index = max(range(len(tabs)), key=lambda i: contacts[i])
    assert contacts[index] > .5, (name, 'no sound tab anchor')
    tab, y = tabs[index], candidates[index]
    envelope = part.makeBox(bounds.XLength, bounds.YLength, bounds.ZLength,
                            app.Vector(bounds.XMin, bounds.YMin, bounds.ZMin))
    tab = tab.cut(envelope.cut(original))
    result = original.fuse(tab)
    # 0.8 mm strokes, 4 mm tall, 0.6 mm raised. Slight pixel overlaps avoid
    # edge-only unions; all strokes are embedded 0.02 mm into the tab.
    tx = edge-10 if side < 0 else edge+3
    for char_index, char in enumerate(code):
        for row, pixels in enumerate(GLYPHS[char]):
            for col, pixel in enumerate(pixels):
                if pixel == '0':
                    continue
                py = row if underside else 4-row
                block = part.makeBox(.82, .82, .62, app.Vector(
                    tx+char_index*3.2+col*.8, y+1.5+py*.8,
                    z-.6 if underside else z+thickness-.02))
                result = result.fuse(block)
    result = result.removeSplitter()
    assert result.isValid() and len(result.Solids) == 1, name
    assert original.cut(result).Volume < 1e-6, (name, 'original material lost')
    # No added material inside the original envelope: the anchor is wholly
    # embedded in a solid edge. This protects holes and mating surfaces.
    assert result.cut(original).common(envelope).Volume < 1e-6, (name, 'anchor intrusion')
    return result, dict(id=code, raised_mm=.6, stroke_mm=.8, tab_mm=[12, 7, thickness])
