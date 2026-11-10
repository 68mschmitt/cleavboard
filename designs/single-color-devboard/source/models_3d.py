#!/usr/bin/env python3
"""Attach bundled models, preserving every non-model PCB byte."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '${KIPRJMOD}/Cleaver-White.3dshapes/'
MODELS = {
    'HanElectricity_CPG151101S11-16': ['SW_Cherry_MX_Plate.wrl', 'SW_Hotswap_Kailh_MX.wrl'],
    'YD_RP2040': ['YD_RP2040_Approx.wrl'],
    'BL-HZ333H-L21-TRE_Reverse': ['BL-HZ333H-L21-TRE_Approx.wrl'],
    'C_0805': ['C_0805_2012Metric.wrl'],
    'R_0805': ['R_0805_2012Metric.wrl'],
    'D_SOD123': ['D_SOD-123.wrl'],
    'PTC_1206': ['Fuse_1206_3216Metric.wrl'],
    'TPS2553': ['SOT-23-6.wrl'], 'SOT-23': ['SOT-23.wrl'],
    'TestPad': [], 'MountingHole_M2': [], 'Fiducial': [],
    'TavianaTactical_34mm': [],
}


def form_end(text, start):
    depth = 0
    quoted = escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if escaped:
            escaped = False
        elif quoted and c == '\\':
            escaped = True
        elif c == '"':
            quoted = not quoted
        elif not quoted:
            depth += (c == '(') - (c == ')')
            if depth == 0:
                return i + 1
    raise ValueError('Unclosed form')


def without_models(text):
    spans = [(m.start(), form_end(text, m.start()))
             for m in re.finditer(r'\(model\s', text)]
    for start, end in reversed(spans):
        text = text[:start] + text[end:]
    return text


def attach(text, name):
    original = without_models(text)
    for path in re.findall(r'\(model\s+"([^"]+)"', text):
        if not path.startswith(PREFIX):
            raise ValueError(f'Refusing unfamiliar model {path}')
    models = ''.join(
        f'(model "{PREFIX}{file}" (offset (xyz 0 0 0)) '
        '(scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
        for file in MODELS[name])
    end = original.rfind(')')
    result = original[:end] + models + original[end:]
    assert without_models(result) == original
    return result


def main():
    for files in MODELS.values():
        for file in files:
            assert (ROOT / 'Cleaver-White.3dshapes' / file).is_file(), file
    for name in MODELS:
        file = ROOT / 'Cleaver-White.pretty' / (name + '.kicad_mod')
        text = file.read_text()
        updated = attach(text, name)
        if updated != text:
            file.write_text(updated)
    pcb = ROOT / 'Cleaver-White.kicad_pcb'
    text = pcb.read_text()
    original = without_models(text)
    matches = list(re.finditer(r'\(footprint "Cleaver-White:([^"]+)"', text))
    counts = {}
    for m in reversed(matches):
        name = m.group(1)
        end = form_end(text, m.start())
        text = text[:m.start()] + attach(text[m.start():end], name) + text[end:]
        counts[name] = counts.get(name, 0) + 1
    assert without_models(text) == original, 'Non-model PCB content changed'
    assert sum(counts[n] for n in counts if MODELS[n]) == 477
    if pcb.read_text() != text:
        pcb.write_text(text)
    report = {
        'populated_footprints': 477,
        'model_instances': sum(counts[n] * len(MODELS[n]) for n in counts),
        'non_model_pcb_sha256': hashlib.sha256(original.encode()).hexdigest(),
        'pcb_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
        'non_model_content_preserved': True,
        'footprints': counts,
    }
    (ROOT / 'validation/models-3d.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
