// SPDX-License-Identifier: GPL-2.0-or-later
#include QMK_KEYBOARD_H
#include "usb_device_state.h"

static bool led_powered;

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
