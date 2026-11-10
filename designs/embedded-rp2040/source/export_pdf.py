#!/usr/bin/env python3
"""Export the authoritative schematic and four readable controller detail pages.
Requires KiCad CLI and pypdf. All output remains within this project.
"""
from pathlib import Path
import subprocess
from pypdf import PdfReader,PdfWriter
from pypdf.generic import RectangleObject
ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/'Cleaver-Embedded-schematic.pdf'
subprocess.run(['kicad-cli','sch','export','pdf','--output',str(pdf),str(ROOT/'Cleaver-Embedded.kicad_sch')],check=True)
writer=PdfWriter()
for left,right in [(10,295),(310,595),(610,895),(910,1185)]:
    page=PdfReader(pdf).pages[0]
    scale=float(page.mediabox.width)/1189
    page.cropbox=RectangleObject([left*scale,(1189-745)*scale,right*scale,(1189-510)*scale])
    writer.add_page(page)
with (ROOT/'Cleaver-Embedded-controller.pdf').open('wb') as f:writer.write(f)
