#pragma once

// LED power MUST come from the raw USB VBUS tap at TP1, not module Vout.
// Keep the 8/255 cap until total current and rail voltage are measured.
#define RGB_MATRIX_DEFAULT_VAL 8
#define RGB_MATRIX_LED_COUNT 117
#define ENABLE_RGB_MATRIX_CYCLE_LEFT_RIGHT
#define ENABLE_RGB_MATRIX_SOLID_REACTIVE_SIMPLE
#define RGB_MATRIX_KEYPRESSES
#define WS2812_TIMING 1250
#define WS2812_T0H 350
#define WS2812_T1H 700
#define WS2812_TRST_US 280
#define LED_POWER_PIN GP28
#define CLEAVER_CAPS_LED 61
#define CLEAVER_NUM_LED 34
#define CLEAVER_SCROLL_LED 1
