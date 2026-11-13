// SPDX-License-Identifier: GPL-2.0-or-later
#include QMK_KEYBOARD_H
#include "color.h"
#include "usb_device_state.h"

static bool led_powered;

#if defined(VIALRGB_ENABLE) && !defined(VIALRGB_NO_DIRECT)
// Vial's direct effect stores one HSV value per physical pixel.
extern HSV g_direct_mode_colors[RGB_MATRIX_LED_COUNT];
#endif

void keyboard_pre_init_kb(void) {
    // R2 keeps the supply off even before firmware starts or in the bootloader.
    setPinOutput(LED_POWER_PIN);
    writePinLow(LED_POWER_PIN);
    led_powered = false;
    keyboard_pre_init_user();
}

void housekeeping_task_kb(void) {
    const bool allow_leds = usb_device_state_get_configure_state() == USB_DEVICE_STATE_CONFIGURED &&
                            rgb_matrix_is_enabled() && !rgb_matrix_get_suspend_state();
    if (allow_leds && !led_powered) {
        writePinHigh(LED_POWER_PIN);
        // Let the current-limited TPS2553 start and the rail settle before
        // relying on a complete frame. The PIO driver refreshes frames normally.
        wait_ms(40);
        led_powered = true;
    } else if (!allow_leds && led_powered) {
        writePinLow(LED_POWER_PIN);
        led_powered = false;
    }
    housekeeping_task_user();
}

void suspend_power_down_kb(void) {
    // QMK may stop housekeeping while suspended: disconnect the LED load here.
    writePinLow(LED_POWER_PIN);
    led_powered = false;
    suspend_power_down_user();
}

void suspend_wakeup_init_kb(void) {
    // Re-enable only after USB is configured and housekeeping runs again.
    suspend_wakeup_init_user();
}

bool rgb_matrix_indicators_advanced_kb(uint8_t led_min, uint8_t led_max) {
    if (!rgb_matrix_indicators_advanced_user(led_min, led_max)) {
        return false;
    }
    // A steady badge follows the user's hue/saturation/brightness even during
    // reactive key effects. Only these four pixels receive the 4x gain; key
    // brightness and the protected supply's USB/suspend gating are unchanged.
    for (uint8_t i = CLEAVER_LOGO_FIRST_LED; i < RGB_MATRIX_LED_COUNT; ++i) {
        if (i < led_min || i >= led_max) {
            continue;
        }
        HSV hsv = rgb_matrix_get_hsv();
#if defined(VIALRGB_ENABLE) && !defined(VIALRGB_NO_DIRECT)
        if (rgb_matrix_get_mode() == RGB_MATRIX_VIALRGB_DIRECT) {
            hsv = g_direct_mode_colors[i];
        }
#endif
        const uint8_t value = hsv.v > RGB_MATRIX_MAXIMUM_BRIGHTNESS ? RGB_MATRIX_MAXIMUM_BRIGHTNESS : hsv.v;
        hsv.v = (uint16_t)value * CLEAVER_LOGO_MAX_BRIGHTNESS / RGB_MATRIX_MAXIMUM_BRIGHTNESS;
        const RGB rgb = hsv_to_rgb(hsv);
        rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
    }
    // Reuse the actual lock keys' LEDs; no extra LEDs beneath the MCU module.
    const led_t state = host_keyboard_led_state();
    const uint8_t indices[] = {CLEAVER_CAPS_LED, CLEAVER_NUM_LED, CLEAVER_SCROLL_LED};
    const bool active[] = {state.caps_lock, state.num_lock, state.scroll_lock};
    for (uint8_t i = 0; i < 3; ++i) {
        if (active[i] && indices[i] >= led_min && indices[i] < led_max) {
            rgb_matrix_set_color(indices[i], 0, RGB_MATRIX_MAXIMUM_BRIGHTNESS, 0);
        }
    }
    return true;
}
