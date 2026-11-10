# Power design and limits

## What the module actually exposes

The VCC-GND/YD **V1.1 schematic**, mirrored at
https://github.com/initdc/YD-RP2040 and saved in `references/YD-RP2040-V1.1.pdf`,
shows:

```text
USB VBUS -> BAT54C anode 1 -> common cathode 3 -> V+ -> header pin 40 (Vout)
VIN pin39 -> BAT54C anode 2 -------------------+
                                              +-> module F1 -> ME6215C33M5G -> 3V3
```

Thus pin40 is upstream of the module's regulator fuse, but **downstream of the
BAT54C**. The USB-fed diode carries **controller plus lighting current**. Pin39
is a second diode input; it is not a raw VBUS output. Pin36's 3V3 is regulated
and gives poor white-LED headroom. Neither is used for the carrier load.

The mirror does not identify the BAT54C manufacturer or a guaranteed continuous
header-output rating. Common documented BAT54C variants specify **200 mA forward
current**, approximately **200–250 mW at 25°C** and thermal resistance around
**430–500 K/W**, with temperature derating. These are component absolute limits,
not an unrestricted module output rating. The exact user's V1.3 circuit and
installed diode remain a **physical identification/qualification check**. Do not
infer its continuous rating from the regulator's larger output capability.

## Chosen circuit

```text
U1 pin40 -> F1 1206L020YR -> U3 TPS2553DBVR -> LED_5V
                                          | 117 parallel branches:
                                          +-> 3.9k 1% -> white LED -> LED_RETURN
GP27 -> R1 330R -> Q1 AO3400A gate                       |
                   R3 100k to GND                       Q1 drain
                                                       Q1 source -> GND
GP28 -> U3 EN; R2 100k to GND
U3 ILIM tied to U3 IN (FUSED_5V), not to a guessed out-of-range resistor.
```

- **TPS2553 datasheet §8.2.2/current-limit programming** explicitly permits ILIM
  tied to IN. The electrical table gives **50/75/100 mA min/typ/max**, including
  output-short operation. This is the primary downstream fault/current control.
  Its ordinary resistor mode only supports 15–232 kΩ; using 300 kΩ for a lower
  limit would be outside the documented range and was rejected.
- F1 is **1206L020YR**, 0.20 A hold / 0.42 A trip, 0.65–2.6 Ω resistance at the
  stated datasheet conditions. It is retained as secondary carrier protection,
  replacing the old 0.5 A PTC. **It is not fast enough or low enough to guarantee
  BAT54C protection.** A short before U3, or U3 failed short, is outside U3's
  protection. Such assembly faults must be found before module-powered bring-up.
- **C1 1 µF SMD** is immediately on the U3 input rail. The ILIM-to-IN arrangement
  specifically calls for low-ESR input bypassing. **C2 22 µF SMD** is downstream
  of U3. The 470 µF radial capacitor and 117 RGB decouplers are unnecessary for
  this resistor-fed, low-current LED load and are removed. C2 supplies switching
  edges while U3 responds; it is not sized to sustain a whole PWM-on interval
  independently. Verify actual effective capacitance/ripple under DC bias.
- AO3400A has **48 mΩ maximum RDS(on) at VGS=2.5 V**, so it is qualified for the
  3.3 V gate signal; threshold voltage alone was not used as a switching rating.
  At 100 mA, 48 mΩ corresponds to only 0.48 mW at the stated datasheet condition.
- R1 reduces gate-edge current/ringing. Physical 100 kΩ pull-downs keep both
  the high-side supply and low-side MOSFET off through reset/BOOTSEL. Firmware
  generates about 1 kHz hardware PWM and enables the supply only after USB
  configuration, with a non-blocking 20 ms settling interval.
- U3 provides reverse-voltage protection; the module diode also blocks reverse
  current toward USB. There is **no external-power connector**, and VIN/3V3 are
  NC. Do not inject power at the test pads or use a second supply. LED current
  never flows through a GPIO. MOSFET gate and EN interfaces do not expose the
  GPIO to the LED rail.

## Calculated budget — not measured

At 100% PWM, an illustrative operating point is Vout=4.6 V and LED Vf=2.6 V at
low current. With one 3.9 kΩ resistor per branch, the ideal branch current is
**0.513 mA**, totaling **60.0 mA**. Including a 2.6 Ω PTC and approximately
0.1 Ω U3 path in the shared branch gives about **55.5 mA total / 0.475 mA per
LED**. The Vf and rail values here are assumptions for sizing, not low-current
bin guarantees. Each resistor dissipates about 1 mW in this example.

| Case | Calculation / consequence |
|---|---|
| 0.5 mA × 117 | 58.5 mA, plausible near the 75 mA typical limiter setting |
| Minimum limiter bin | 50 mA total; approximately 0.427 mA average per LED; brightness may compress at high settings |
| 1 mA × 117 | 117 mA; **not supported** by this 100 mA maximum branch limit |
| Conservative healthy-LED scenario | 5.25 V rail, no assumed diode drop, Vf=2.0 V, resistor −1%: 0.842 mA/LED or 98.5 mA before shared drops |
| No guaranteed Vf minimum | Resistor-only absolute bound using Vf=0 is 1.36 mA/branch / 159 mA aggregate; **U3 limits the aggregate to ≤100 mA** in steady state |
| Resistor fault dissipation bound | 5.25² / 3861 = 7.14 mW, well below the selected 125 mW resistor rating |
| Module allocation | **50 mA design allocation**, including RP2040, flash, regulator, onboard LEDs and matrix; must be measured, not a documented module maximum |
| Proposed upper operating budget | 50 mA module + 100 mA lighting + approximately 0.2 mA control/IQ = **150.2 mA** |
| USB descriptor | 200 mA, leaving allocation margin; does not enforce or prove actual current |
| Before configuration / suspend | Lighting disabled in hardware; module's own current remains and must be measured separately |

1% resistor tolerance is included above. ±100 ppm/°C resistor temperature drift
adds about ±0.25% over a 25°C change; it is much smaller than white-LED Vf spread
or the 50–100 mA limiter range. Neither minimum brightness nor color consistency
at 0.4–0.6 mA is specified by the LED's 5 mA photometric rating. **Visible white
brightness and keycap uniformity remain untested until a sample is assembled.**

Selected LED **BrtLed BL-HZ333H-L21-TRE / C5123487**: 20 mA continuous maximum,
Vf typical 2.8 V / maximum 3.2 V at 5 mA, intensity minimum 63 / typical 120 mcd
at 5 mA. The 3.9 kΩ resistors and limiter are retained: 5 mA is a datasheet test
point, not this board's operating target (117 × 5 mA would be 585 mA). The
resistor-only bound, even for a shorted LED, is 1.36 mA per branch at 5.25 V and
−1% resistance. The aggregate limiter, rather than LED ratings, constrains this
header-powered design. The low-current Vf=2.6 V sizing assumption above is not a
guaranteed BrtLed bin value.

The shared module diode's forward drop/thermal behavior is the important
remaining power constraint. As a stress estimate, 150 mA × 0.8 V is 120 mW;
at 500 K/W that is roughly 60°C rise. A 1 V drop would instead mean 150 mW and
75°C rise. Those examples show why a 200 mA absolute rating alone is insufficient.
Initially qualify at **ambient ≤40°C**, module baseline ≤50 mA, full-board USB
current within the budget, and diode temperature/junction estimate with margin
to the identified diode's datasheet. The diode's Vf above 100 mA and exact
module thermal resistance are **not guaranteed by the available module manual**.

Higher-value 4.7 kΩ or 5.6 kΩ branch resistors can lower normal current; update
the source/BOM and reassess brightness if selecting either. Lower values are not
approved here. If the actual module exceeds the allocation or its diode fails
thermal qualification, the header-only power assumption must change (a module
with a documented suitably protected rail, or a revised supply architecture).
Do not defeat the diode or raise the limiter. No extra wire is required by this
implemented circuit, but an unconditional guarantee for all undocumented YD
module revisions is not supported by the available evidence.

## USB/suspend and prototype checks

QMK backlight defaults off. The supply is disabled on loss of configuration and
in the immediate suspend hook; resume starts through configuration/settling checks.
The module's factory power LED and regulator remain powered. **Full-device USB
suspend-current compliance is unverified** and may require module/firmware
changes even though the carrier LED branch is off. Do not report a USB descriptor
or successful UF2 build as measured USB compliance.

Bring up with current-limited USB: inspect shorts before attaching the module;
confirm U1 pin40 polarity/top orientation, matrix, and one LED first. Measure
module-only current in run/BOOTSEL/suspend, branch input current, total USB current,
Vout and LED rail ripple at each PWM step, limiter startup/short response, and
module diode temperature. Then test 117 keys/chords, disconnect/reconnect,
suspend/resume, USB-A-to-C and C-to-C. The normal production module needs no wire
modification; temporary bench probes are instrumentation only.
