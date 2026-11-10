"""Exact replacement identities shared by KiCad generation and purchasing exports."""
SELECTED = {
    'MX': {
        'Manufacturer': 'HanElectricity',
        'MPN': 'CPG151101S11-16',
        'LCSC Part #': 'C41430893',
        'footprint': 'HanElectricity_CPG151101S11-16',
        'package': 'MX hot-swap socket',
        'Source': 'https://jlcpcb.com/partdetail/HanElectricity-CPG151101S1116/C41430893',
        'Datasheet': 'https://datasheet.lcsc.com/datasheet/pdf/d953a8b0b623247f3341ebcfbaa2e88f.pdf',
    },
    'WhiteLED': {
        'Manufacturer': 'BrtLed',
        'MPN': 'BL-HZ333H-L21-TRE',
        'LCSC Part #': 'C5123487',
        'footprint': 'BL-HZ333H-L21-TRE_Reverse',
        'package': '1206 reverse-mount white LED',
        'Source': 'https://jlcpcb.com/partdetail/5717311-BL_HZ333H_L21TRE/C5123487',
        'Datasheet': 'https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2208051800_BrtLed-Bright-LED-Elec-BL-HZ333H-L21-TRE_C5123487.pdf',
    },
}


def fields(part):
    result = {k: v for k, v in SELECTED.get(part['kind'], {}).items()
              if k not in {'footprint', 'package'}}
    if 'key_label' in part:
        result['Key'] = part['key_label']
    return result
