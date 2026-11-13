#pragma once

// Waveshare RP2040-Plus: USB VBUS pin 40 -> F1 -> TPS2553 -> LED_5V.
// W25Q32JV (4MB) uses QMK's default W25Q080-compatible stage-2 bootloader.
// Keep EEPROM in the first 2MB, also valid on the 16MB variant and compatible
// with earlier Cleaver builds' persistent Vial settings.
#define WEAR_LEVELING_RP2040_FLASH_SIZE (2 * 1024 * 1024)
// Keep the 8/255 cap until total current and rail voltage are measured.
#define RGB_MATRIX_DEFAULT_VAL 8
#define RGB_MATRIX_LED_COUNT 121
#define CLEAVER_LOGO_FIRST_LED 117
#define CLEAVER_LOGO_MAX_BRIGHTNESS 32
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
