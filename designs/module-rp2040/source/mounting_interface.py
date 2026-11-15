"""Rev0.11 removable PCB/plate cartridge. Coordinates: PCB top view, millimetres.

P sites pass base posts through the PCB; A sites fasten the PCB upward to plate
bosses. All sites were selected against saved routed copper and physical parts.
"""
REVISION = '0.11'
BASE_POSTS = [
    (8.25, 19.0), (78.0, 22.5), (160.0, 22.5), (237.0, 24.75),
    (324.0, 23.0), (112.0, 134.25), (311.75, 104.0), (349.25, 83.25),
    (373.0, 84.0), (40.0, 134.5), (266.25, 137.0), (436.5, 134.0),
]
PCB_ATTACHMENTS = [
    (48.0, 23.0), (108.75, 22.5), (199.0, 23.25), (286.0, 22.75),
    (359.0, 23.5), (24.75, 91.5), (190.0, 107.5), (318.0, 78.25),
    (374.75, 109.75), (90.0, 134.25), (286.0, 124.25), (390.0, 134.5),
]
POST_DIAMETER = 6.0
PASS_THROUGH_DRILL = 7.0
PCB_SCREW_DRILL = 2.2
PLATE_SCREW_DRILL = 2.8
PLATE_BOSS_DIAMETER = 6.4
PLATE_BOSS_ROOT_DIAMETER = 7.6
SHORT_INSERT_LENGTH = 2.5
SHORT_INSERT_PILOT_DEPTH = 2.8

LEGACY_MOUNTING_HOLES = [
    (4, 4), (110, 23.8), (220, 23.8), (330, 23.8), (395, 26),
    (313, 70), (4, 143), (90, 138), (263, 138), (365, 138), (448, 138),
]


def mounting_specs():
    return [
        dict(reference=f'H{i+1}', role='base_post_pass_through' if i < len(BASE_POSTS) else 'pcb_to_plate',
             x=x, y=y, drill_mm=PASS_THROUGH_DRILL if i < len(BASE_POSTS) else PCB_SCREW_DRILL,
             reserve_radius_mm=4.0 if i < len(BASE_POSTS) else 3.2,
             footprint='MountingHole_Post7' if i < len(BASE_POSTS) else 'MountingHole_M2')
        for i, (x, y) in enumerate(BASE_POSTS+PCB_ATTACHMENTS)
    ]


def legacy_mounting_specs():
    return [dict(reference=f'H{i}', x=x, y=y, drill_mm=2.2, reserve_radius_mm=3.)
            for i, (x, y) in enumerate(LEGACY_MOUNTING_HOLES, 1)]
