"""Shared rev0.9 illuminated badge interface, in PCB top-view millimetres.

The 2 x 1 inch face needs an 8 mm deeper plate and enclosure front. The PCB and
key positions stay fixed; the badge moves 1 mm forward to clear keycap sweeps.
"""

LOGO_X, LOGO_Y = 227.6475, 139.1125
APERTURE = (51.2, 25.8)
INSERT = (50.8, 25.4)
FLANGE = (53.8, 28.4)
LIGHT_BORE = (48.8, 23.4)
FRONT_EXTENSION = 8.0
LED_OFFSETS = [(-19.5, 1.5), (-6.5, 1.5), (6.5, 1.5), (19.5, 1.5)]
KEY_LED_COUNT = 117
RGB_LED_COUNT = KEY_LED_COUNT + len(LED_OFFSETS)
LOGO_MAX_BRIGHTNESS = 32


def rectangle(size):
    from shapely import box
    width, height = size
    return box(LOGO_X-width/2, LOGO_Y-height/2, LOGO_X+width/2, LOGO_Y+height/2)


def logo_leds():
    """Append four non-key pixels without renumbering any existing key pixel."""
    return [dict(led_ref=f'LED{i+118:03d}', cap_ref=f'C{i+218}',
                 x=LOGO_X+dx, y=LOGO_Y+dy,
                  cap_x=LOGO_X+dx, cap_y=LOGO_Y-3.5,
                 led_index=KEY_LED_COUNT+i, rgb_in=f'RGB_{KEY_LED_COUNT+i:03d}',
                 rgb_out=f'RGB_{KEY_LED_COUNT+i+1:03d}' if i < len(LED_OFFSETS)-1 else None)
            for i, (dx, dy) in enumerate(LED_OFFSETS)]
