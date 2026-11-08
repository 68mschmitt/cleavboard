#pragma once

#define MATRIX_ROWS 7
#define MATRIX_COLS 17
#define MATRIX_ROW_PINS { GP0, GP1, GP2, GP3, GP4, GP5, GP6 }
#define MATRIX_COL_PINS { GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14, GP15, GP16, GP17, GP18, GP19, GP20, GP21, GP22, GP26 }
#define DIODE_DIRECTION ROW2COL

#define WS2812_DI_PIN GP27
#define RGB_MATRIX_LED_COUNT 117
// Conservative USB-only starting point; increase only after measuring total current.
#define RGB_MATRIX_MAXIMUM_BRIGHTNESS 12
#define USB_MAX_POWER_CONSUMPTION 500
