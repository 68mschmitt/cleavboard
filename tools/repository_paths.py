"""Translate pre-organization repository paths for historical comparisons."""

MODULE = "designs/module-rp2040"
EMBEDDED = "designs/embedded-rp2040"
WHITE = "designs/single-color-devboard"
LAYOUT = "assets/layout"

# Most-specific paths first; directory mappings include their trailing slash.
MOVED_PATHS = (
    ("kicad/BOM.csv", f"{MODULE}/manufacturing/BOM.csv"),
    ("kicad/Cleaver.stl", f"{MODULE}/mechanical/Cleaver.stl"),
    ("kicad/", f"{MODULE}/"),
    ("scripts/", f"{MODULE}/source/"),
    ("mechanical/", f"{MODULE}/mechanical/"),
    ("manufacturing/", f"{MODULE}/manufacturing/"),
    ("Cleaver-gerbers.zip", f"{MODULE}/manufacturing/archive/Cleaver-gerbers.zip"),
    ("usb-vbus-ref-pic.jpg", f"{MODULE}/references/usb-vbus-ref-pic.jpg"),
    ("tavi-tac.png", "assets/artwork/taviana/tavi-tac.png"),
    ("artwork/", "assets/artwork/"),
    ("plate-2026-11-07T22_24_25.197Z/keyboard-layout(1).json", f"{LAYOUT}/keyboard-layout.json"),
    ("plate-2026-11-07T22_24_25.197Z/keyboard-layout(1).svg", f"{LAYOUT}/keyboard-layout.svg"),
    ("plate-2026-11-07T22_24_25.197Z/plate-2026-11-07T22_24_25.197Z.dxf", f"{LAYOUT}/original-plate.dxf"),
    ("plate-2026-11-07T22_24_25.197Z/plate-2026-11-07T22_24_27.294Z.svg", f"{LAYOUT}/original-plate.svg"),
    ("plate-2026-11-07T22_24_25.197Z/", f"{LAYOUT}/"),
    *[(f"{project}/BOM.csv", f"{project}/manufacturing/BOM.csv")
      for project in (EMBEDDED, WHITE)],
    *[(f"{EMBEDDED}/{name}", f"{EMBEDDED}/manufacturing/rev0.2/{name}")
      for name in ("Cleaver-Embedded-embedded-0.2-gerbers.zip",
                   "Cleaver-Embedded-JLCPCB-BOM-no-C5.csv",
                   "Cleaver-Embedded-JLCPCB-CPL.csv", "Cleaver-Embedded-CPL.csv")],
    *[(f"{project}/{name}", f"{project}/docs/{name}")
      for project, names in (
          (EMBEDDED, ("Cleaver-Embedded-schematic.pdf", "Cleaver-Embedded-controller.pdf")),
          (WHITE, ("Cleaver-White-schematic.pdf", "Cleaver-White-schematic-details.pdf")))
      for name in names],
)


def current_path(path):
    """Map a historical root-relative POSIX path to its current location."""
    for old, new in MOVED_PATHS:
        if path == old or (old.endswith("/") and path.startswith(old)):
            return new + path[len(old):]
    return path
