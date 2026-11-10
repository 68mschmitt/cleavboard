#!/usr/bin/env python3
"""Independent RP2040 pinout, key-layout, and schematic/PCB interface checks.

Uses the actual KiCad files, not the variant's generator definitions. Requires
KiCad's pcbnew Python module and kicad-cli. This complements ERC/DRC; it does
not establish physical routing connectivity or manufacturing readiness.
RP2040 pin numbers follow Raspberry Pi's QFN-56 datasheet (pad 57 is ground).
"""

import argparse
import csv
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
# Dedicated QSPI/USB pins are deliberately separate from the GPIO table.
GPIO_PINS = {
    **{gpio: gpio + 2 for gpio in range(8)},
    **{gpio: gpio + 3 for gpio in range(8, 16)},
    **{gpio: gpio + 11 for gpio in range(16, 22)},
    **{gpio: gpio + 12 for gpio in range(22, 30)},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", type=Path,
        default=ROOT / "designs/embedded-rp2040/Cleaver-Embedded.kicad_pro",
    )
    args = parser.parse_args()
    project = args.project.resolve()
    board = pcbnew.LoadBoard(str(project.with_suffix(".kicad_pcb")))
    # Compare inherited geometry with this variant's frozen input, not a newer
    # module revision whose sockets and component-side metadata have evolved.
    original = pcbnew.LoadBoard(str(project.parent / "source/legacy-base.kicad_pcb"))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    old_footprints = {fp.GetReference(): fp for fp in original.GetFootprints()}

    # Composite MX footprints describe the top-side switch mechanically while
    # their soldered socket pads are underneath. Inspect pad layers, not just
    # the footprint's nominal side, to verify one-sided SMD assembly.
    top_smd = []
    top_paste = []
    with (project.parent / "manufacturing/BOM.csv").open(newline="") as bom_file:
        bom = {row["reference"]: row for row in csv.DictReader(bom_file)}
    for ref, fp in footprints.items():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and pad.IsOnLayer(pcbnew.F_Cu):
                top_smd.append(f"{ref}.{pad.GetNumber()}")
            if pad.IsOnLayer(pcbnew.F_Paste):
                top_paste.append(f"{ref}.{pad.GetNumber() or 'paste-window'}")
            if pad.IsOnLayer(pcbnew.B_Paste):
                require(ref in bom and bom[ref]["side"] == "B",
                        f"Underside soldered component {ref} must have BOM side B")
        require(not any(item.GetLayer() == pcbnew.F_Paste for item in fp.GraphicalItems()),
                f"Top-side paste graphics in {ref}")
    require(not top_smd, f"Top-side SMD pads remain: {top_smd}")
    require(not top_paste, f"Top-side solder paste remains: {top_paste}")
    require(not any(item.GetLayer() == pcbnew.F_Paste for item in board.GetDrawings()),
            "Top-side solder-paste drawing remains")

    def one_matching(predicate, description):
        matches = [fp for fp in footprints.values() if predicate(fp)]
        require(len(matches) == 1, f"Expected one {description}, found {len(matches)}")
        return matches[0].GetReference()

    mcu = one_matching(lambda fp: fp.GetValue().upper() == "RP2040", "bare RP2040")
    flash = one_matching(lambda fp: "W25Q32" in fp.GetValue().upper(), "4 MB Winbond flash")
    pads = {}
    for ref, fp in footprints.items():
        for pad in fp.Pads():
            if not pad.GetNumber():
                continue  # Unnumbered paste windows and mechanical holes are not pins.
            key = (ref, pad.GetNumber())
            name = pad.GetNetname()
            if key in pads:
                require(pads[key] == name, f"Duplicate pad numbers disagree: {key}")
            pads[key] = name

    def net(ref, number):
        value = pads[(ref, str(number))]
        require(value and not value.startswith("unconnected-"), f"Disconnected {ref}.{number}")
        return value

    def same(*connections):
        names = {net(ref, number) for ref, number in connections}
        require(len(names) == 1, f"Expected shared net: {connections}; got {names}")

    ground = net(mcu, 57)
    supply = net(mcu, 1)
    core = net(mcu, 45)
    require(len({ground, supply, core}) == 3, "Ground, 3.3 V and 1.1 V must be distinct")
    same(*[(mcu, pin) for pin in (1, 10, 22, 33, 42, 43, 44, 48, 49)])
    same(*[(mcu, pin) for pin in (23, 45, 50)])
    same((mcu, 19), (mcu, 57))  # TESTEN must be grounded.
    require(net(mcu, 43) != ground, "ADC_AVDD must be powered even with no analog inputs")
    require({str(pin) for pin in range(1, 58)} ==
            {number for ref, number in pads if ref == mcu}, "Incorrect RP2040 footprint pads")

    # Winbond SOIC-8/QSPI interface: SS, IO1, IO2, GND, IO0, CLK, IO3, VCC.
    for flash_pin, mcu_pin in {1: 56, 2: 55, 3: 54, 4: 57, 5: 53, 6: 52, 7: 51, 8: 1}.items():
        same((flash, flash_pin), (mcu, mcu_pin))

    connector = one_matching(lambda fp: fp.GetValue() == "HRO TYPE-C-31-M-12", "USB-C connector")
    regulator = one_matching(lambda fp: fp.GetValue() == "AP2112K-3.3TRG1", "3.3 V regulator")
    esd = one_matching(lambda fp: fp.GetValue() == "USBLC6-2SC6", "USB ESD protection")
    same(*[(connector, pin) for pin in ("A4", "A9", "B4", "B9")],
         (regulator, 1), (regulator, 3), (esd, 5), ("F1", 1))
    same(*[(connector, pin) for pin in ("A1", "A12", "B1", "B12", "S1")],
         (regulator, 2), (esd, 2), (mcu, 57))
    same((regulator, 5), (mcu, 1))
    require(len({net(connector, "A4"), supply, core, ground}) == 4,
            "VBUS, regulator output, core and ground must be distinct")
    for ref, cc_pin in (("R12", "A5"), ("R13", "B5")):
        require(footprints[ref].GetValue() == "5.1k 1%", f"Incorrect USB-C pulldown {ref}")
        same((ref, 1), (connector, cc_pin))
        same((ref, 2), (mcu, 57))
    require(len({net(connector, "A5"), net(connector, "B5"), ground}) == 3,
            "CC1 and CC2 require independent pulldowns")
    same((connector, "A6"), (connector, "B6"), (esd, 1), (esd, 6), ("R10", 2))
    same((connector, "A7"), (connector, "B7"), (esd, 3), (esd, 4), ("R11", 2))
    same(("R10", 1), (mcu, 47))
    same(("R11", 1), (mcu, 46))
    for ref in ("R10", "R11"):
        require(footprints[ref].GetValue() == "27R 1%", f"Incorrect USB series resistor {ref}")
    require(len({net(connector, "A6"), net(connector, "A7"), net(mcu, 46), net(mcu, 47)}) == 4,
            "USB polarities and both sides of each series resistor must be distinct")

    info = json.loads((project.parent / "firmware/keyboard.json").read_text())
    rows, cols = info["matrix_pins"]["rows"], info["matrix_pins"]["cols"]
    require(len(rows) == 8 and len(cols) == 16, "Expected 8x16 matrix")
    require(len(set(rows + cols)) == 24, "Matrix GPIOs overlap")
    require(info["diode_direction"] == "ROW2COL", "Diode direction changed")
    require(info["rgb_matrix"]["max_brightness"] == 8, "Conservative brightness cap changed")
    require(info["ws2812"]["pin"] == "GP27", "RGB data GPIO changed")
    require(len(info["rgb_matrix"]["layout"]) == 117, "RGB layout count changed")

    def gpio_pin(name):
        return GPIO_PINS[int(name.removeprefix("GP"))]

    def socket_geometry(fp):
        return sorted((p.GetNumber(), p.GetPosition().x, p.GetPosition().y,
                       p.GetSize().x, p.GetSize().y, p.GetDrillSize().x,
                       p.GetDrillSize().y, int(p.GetAttribute()),
                       p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu))
                      for p in fp.Pads())

    for i in range(117):
        switch, diode = f"SW{i + 1:03d}", f"D{i + 1:03d}"
        row, col = divmod(i, 16)
        same((mcu, gpio_pin(rows[row])), (switch, 1))
        same((mcu, gpio_pin(cols[col])), (diode, 1))
        same((switch, 2), (diode, 2))
        for ref in (switch, diode, f"LED{i + 1:03d}"):
            before, after = old_footprints[ref], footprints[ref]
            require(before.GetPosition() == after.GetPosition(), f"{ref} position changed")
            require(before.GetOrientationDegrees() == after.GetOrientationDegrees(),
                    f"{ref} orientation changed")
            require(before.GetLayer() == after.GetLayer(), f"{ref} board side changed")
        # Composite socket footprints must retain their asymmetric switch holes
        # and underside lands; changing metadata must not mirror the geometry.
        require(socket_geometry(old_footprints[switch]) == socket_geometry(footprints[switch]),
                f"{switch} socket lands or switch-hole geometry changed")
    require(board.GetCopperLayerCount() == 4, "Expected four copper layers")

    # Fresh export tests real schematic readability and actual pad assignments.
    temporary_root = Path("/tmp/opencode")
    with tempfile.TemporaryDirectory(
        prefix="cleaver-interface-", dir=temporary_root if temporary_root.is_dir() else None,
    ) as temporary:
        exported = Path(temporary) / "netlist.xml"
        subprocess.run([
            "kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
            "-o", str(exported), str(project.with_suffix(".kicad_sch")),
        ], check=True)
        schematic = ET.parse(exported).getroot()
        checked = 0
        for electrical_net in schematic.findall("./nets/net"):
            for node in electrical_net.findall("node"):
                key = node.get("ref"), node.get("pin")
                if key[0].startswith("#"):
                    continue
                require(key in pads, f"Schematic pin missing on PCB: {key}")
                require(pads[key] == electrical_net.get("name"),
                        f"Schematic/PCB net mismatch: {key}")
                checked += 1

    print(f"PASS: RP2040 supplies, QSPI/USB pinouts, USB-C power, 117 key circuits/positions, firmware matrix,")
    print(f"      {checked} schematic-to-PCB pin assignments, and underside-only SMD/paste independently checked.")
    print("Run the variant's ERC/DRC checks separately to verify routed connectivity.")


if __name__ == "__main__":
    main()
