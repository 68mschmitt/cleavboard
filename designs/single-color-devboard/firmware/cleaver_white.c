// SPDX-License-Identifier: GPL-2.0-or-later
#include QMK_KEYBOARD_H
#include "hal.h"
#include "usb_device_state.h"

// GP27 = PWM slice 5, output B. GP26 remains ordinary matrix GPIO.
static const PWMConfig white_pwm = {
    .frequency = 1000000,
    .period = 1000,
    .callback = NULL,
    .channels = {{PWM_OUTPUT_DISABLED, NULL}, {PWM_OUTPUT_ACTIVE_HIGH, NULL}},
};
static uint8_t requested_level;
static bool pwm_ready, powered, suspended;
static uint32_t powered_at;

static void lights_off(void) {
    writePinLow(LED_POWER_PIN);
    if (pwm_ready) pwmEnableChannel(&PWMD5, 1, 0);
    powered = false;
}

void keyboard_pre_init_kb(void) {
    // Both outputs have physical 100k pull-downs during reset/BOOTSEL.
    writePinLow(LED_POWER_PIN);
    setPinOutput(LED_POWER_PIN);
    writePinLow(WHITE_PWM_PIN);
    setPinOutput(WHITE_PWM_PIN);
    // Keep the module's ordinary status LED off; onboard RGB is unused.
    writePinLow(GP25);
    setPinOutput(GP25);
    writePinLow(GP23);
    setPinOutput(GP23);
    keyboard_pre_init_user();
}

void backlight_init_ports(void) {
    pwmStart(&PWMD5, &white_pwm);
    pwmEnableChannel(&PWMD5, 1, 0);
    palSetLineMode(WHITE_PWM_PIN, PAL_MODE_ALTERNATE(4));
    pwm_ready = true;
    lights_off();
}

void backlight_set(uint8_t level) {
    requested_level = level > BACKLIGHT_LEVELS ? BACKLIGHT_LEVELS : level;
    if (!requested_level) lights_off();
}

void backlight_task(void) {
    const bool configured = usb_device_state_get_configure_state() == USB_DEVICE_STATE_CONFIGURED;
    if (!pwm_ready || !configured || suspended || !requested_level) {
        lights_off();
        return;
    }
    if (!powered) {
        pwmEnableChannel(&PWMD5, 1, 0);
        writePinHigh(LED_POWER_PIN);
        powered_at = timer_read32();
        powered = true;
    }
    // Non-blocking supply/capacitor startup; PWM remains off until settled.
    if (timer_elapsed32(powered_at) >= 20) {
        pwmEnableChannel(&PWMD5, 1, (1000U * requested_level) / BACKLIGHT_LEVELS);
    }
}

void suspend_power_down_kb(void) {
    suspended = true;
    lights_off();
    suspend_power_down_user();
}

void suspend_wakeup_init_kb(void) {
    suspended = false;
    // backlight_task rechecks configuration and performs startup delay.
    suspend_wakeup_init_user();
}
