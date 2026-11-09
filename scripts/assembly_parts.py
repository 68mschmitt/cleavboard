"""Purchasing identities for the populated underside, checked 2026-11-08.

Manufacturer codes are authoritative, not interchangeable package-name matches.
Catalog listings establish sourcing support, not reserved inventory or DFM approval.
"""
PARTS = {
    'MX': ('Kailh', 'CPG151101S11', 'C2803348', 'SMD Kailh MX socket'),
    'D_SOD123': ('Semtech', '1N4148W', 'C81598', 'SOD-123'),
    'MINI_E': ('OPSCO Optoelectronics', 'SK6812MINI-E', 'C5149201', 'Reverse-mount 3.2x2.8mm'),
    '100nF 50V X7R': ('YAGEO', 'CC0805KRX7R9BB104', 'C49678', '0805'),
    '1uF 50V X7R': ('Samsung Electro-Mechanics', 'CL21B105KBFNNNE', 'C28323', '0805'),
    '22uF 10V X5R': ('Samsung Electro-Mechanics', 'CL21A226MPQNNNE', 'C29277', '0805'),
    '330R': ('UNI-ROYAL', '0805W8F3300T5E', 'C17630', '0805 1%'),
    '100k': ('UNI-ROYAL', '0805W8F1003T5E', 'C149504', '0805 1%'),
    '75k 1%': ('UNI-ROYAL', '0805W8F7502T5E', 'C17819', '0805 1%'),
    'PTC_1206': ('Littelfuse', '1206L050YR', 'C163512', '1206'),
    'LV1T125': ('Texas Instruments', 'SN74LV1T125DBVR', 'C473338', 'SOT-23-5'),
    'TPS2553': ('Texas Instruments', 'TPS2553DBVR', 'C55266', 'SOT-23-6'),
}
USER_ASSEMBLED = {'YD_RP2040', 'C_Radial8', 'WirePad', 'TestPad'}


def purchase(part):
    if part['kind'] in USER_ASSEMBLED:
        return None
    return PARTS.get(part['kind']) or PARTS[part['value']]
