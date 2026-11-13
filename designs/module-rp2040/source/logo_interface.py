"""Shared rev0.8 illuminated badge interface, in PCB top-view millimetres.

The front row is only one key pitch deep. Keep the plate aperture inside its
front edge and the retaining flange inside the cover's locating lip.
"""

LOGO_X, LOGO_Y = 227.6475, 138.1125
APERTURE = 16.4
INSERT = 16.0
FLANGE = 19.0
LIGHT_BORE = 14.0
LED_OFFSETS = [(-4.25, -2.5), (4.25, -2.5), (4.25, 2.5), (-4.25, 2.5)]
KEY_LED_COUNT = 117
RGB_LED_COUNT = KEY_LED_COUNT + len(LED_OFFSETS)
LOGO_MAX_BRIGHTNESS = 32


def square(size):
    from shapely import box
    return box(LOGO_X-size/2, LOGO_Y-size/2, LOGO_X+size/2, LOGO_Y+size/2)


def logo_leds():
    """Append four non-key pixels without renumbering any existing key pixel."""
    return [dict(led_ref=f'LED{i+118:03d}', cap_ref=f'C{i+218}',
                 x=LOGO_X+dx, y=LOGO_Y+dy,
                 cap_x=LOGO_X+(-11.5 if dx < 0 else 11.5),
                 led_index=KEY_LED_COUNT+i, rgb_in=f'RGB_{KEY_LED_COUNT+i:03d}',
                 rgb_out=f'RGB_{KEY_LED_COUNT+i+1:03d}' if i < len(LED_OFFSETS)-1 else None)
            for i, (dx, dy) in enumerate(LED_OFFSETS)]
