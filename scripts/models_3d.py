"""Project-relative model assignments; editing them never changes PCB geometry."""
from __future__ import annotations

import json
import re

from design import ROOT

PREFIX = '${KIPRJMOD}/Cleaver.3dshapes/'
# Models use their native units: millimeters in STEP, 0.1 inch in KiCad VRML.
# The socket is already drawn below a 1.6mm carrier in the source MX assembly;
# do NOT flip the whole mixed front-switch/back-socket footprint.
MODELS = {
    'Kailh_socket_MX': ('SW_Cherry_MX_Plate.wrl','SW_Hotswap_Kailh_MX.wrl'),
    'C_0805': ('C_0805_2012Metric.wrl',),
    'R_0805': ('R_0805_2012Metric.wrl',),
    'D_SOD123': ('D_SOD-123.wrl',),
    'PTC_1206': ('Fuse_1206_3216Metric.wrl',),
    'LV1T125': ('SOT-23-5.wrl',),
    'TPS2553': ('SOT-23-6.wrl',),
    'MINI_E': ('LED_SK6812MINI-E_Reverse.wrl',),
    'YD_RP2040': ('YD_RP2040_Approx.wrl',),
    'C_Radial8': ('C_Radial_D8_H11.5_P3.5.wrl',),
    # TP1 is an exposed wire-soldering pad, not a mounted connector/component.
    'WirePad': (),
}


def form_end(text, start):
    """Find an s-expression end, respecting strings and escaped quotes."""
    depth, quoted, escaped = 0, False, False
    for index in range(start,len(text)):
        c = text[index]
        if escaped:
            escaped = False
            continue
        if quoted and c=='\\':
            escaped = True
            continue
        if c=='"':
            quoted = not quoted
        elif not quoted:
            if c=='(':
                depth += 1
            elif c==')':
                depth -= 1
                if depth==0:
                    return index+1
    raise ValueError('Unclosed KiCad form')


def without_models(text):
    """Remove only complete model lines; leave all other bytes unchanged."""
    spans = []
    for match in re.finditer(r'(?m)^[ \t]*\(model\s',text):
        start = text.index('(',match.start())
        end = form_end(text,start)
        if not text[end:text.index('\n',end) if '\n' in text[end:] else len(text)].strip():
            end = text.index('\n',end)+1 if '\n' in text[end:] else len(text)
        spans.append((match.start(),end))
    for start,end in reversed(spans):
        text = text[:start]+text[end:]
    return text


def model_text(name, indent='  '):
    return '\n'.join(f'''{indent}(model {json.dumps(PREFIX+filename)}
{indent}  (offset (xyz 0 0 0))
{indent}  (scale (xyz 1 1 1))
{indent}  (rotate (xyz 0 0 0))
{indent})''' for filename in MODELS[name])


def replace_models(text, name, indent='  '):
    old_paths = [quoted or bare for quoted,bare in
                 re.findall(r'\(model\s+(?:"([^"]+)"|([^\s()]+))',text)]
    if any(not path.startswith(PREFIX) for path in old_paths):
        raise ValueError(f'{name}: refusing to overwrite an unfamiliar model assignment')
    original = without_models(text)
    end = original.rfind(')')
    line = original.rfind('\n',0,end)+1
    if original[line:end].strip():
        raise ValueError(f'{name}: footprint closing parenthesis must be on its own line')
    models = model_text(name,indent)
    result = original[:line]+(models+'\n' if models else '')+original[line:]
    assert without_models(result)==original, 'Non-model content changed'
    return result


def update_library_models(directory):
    for name in MODELS:
        path = directory/(name+'.kicad_mod')
        text = path.read_text()
        updated = replace_models(text,name)
        if updated!=text:
            path.write_text(updated)


def update_board_models(path):
    text = path.read_text()
    original = without_models(text)
    spans = []
    for match in re.finditer(r'(?m)^(\s*)\(footprint "Cleaver:([^"]+)"',text):
        name = match.group(2)
        if name not in MODELS:
            raise ValueError(f'No model policy for {name}')
        start = text.index('(',match.start())
        end = form_end(text,start)
        # Include the leading indentation so the original closing line and
        # every non-model byte survive insertion verbatim.
        start = text.rfind('\n',0,start)+1
        spans.append((start,end,name))
    if len(spans)!=481:
        raise ValueError(f'Expected 481 footprints, found {len(spans)}')
    for start,end,name in reversed(spans):
        text = text[:start]+replace_models(text[start:end],name,'\t\t')+text[end:]
    assert without_models(text)==original, 'Non-model PCB content changed'
    if path.read_text()!=text:
        path.write_text(text)


def validate_models(board):
    populated = count = 0
    for fp in board.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        expected = [PREFIX+filename for filename in MODELS[name]]
        actual = list(fp.Models())
        assert [model.m_Filename for model in actual]==expected, f'{fp.GetReference()}: incorrect/missing models'
        for model in actual:
            assert model.m_Show, f'{fp.GetReference()}: hidden model'
            for vector,value in ((model.m_Scale,1),(model.m_Offset,0),(model.m_Rotation,0)):
                assert all(abs(getattr(vector,axis)-value)<1e-6 for axis in ('x','y','z')), f'{fp.GetReference()}: unexpected model transform'
            path = ROOT/'kicad'/model.m_Filename.removeprefix('${KIPRJMOD}/')
            assert path.is_file(), f'Missing local model: {path}'
            assert path.with_suffix('.step').is_file(), f'Missing STEP counterpart: {path}'
        count += len(actual)
        populated += bool(actual)
    assert len(list(board.GetFootprints()))==481
    assert (populated,count)==(480,597), (populated,count)
    return dict(populated_footprints=populated,model_instances=count,
                unique_models=len({name for names in MODELS.values() for name in names}),
                intentionally_unmodeled=['TP1: bare wire-soldering pad'])
