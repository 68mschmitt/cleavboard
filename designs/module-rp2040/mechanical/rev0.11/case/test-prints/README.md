# Test prints and assembly aids

Print the relevant small parts here before committing to the full case and plate.
Use **STL** files in the slicer; matching **STEP** files are provided for CAD.

## Embossed fit-set labels

Every test model has a raised ID on an attached external tab. Match the letter;
the number identifies the part within that fit set.

| IDs | Fit together / test against |
| --- | --- |
| **A1 / A2 / A3** | Mounting-stack base / plate / dummy PCB |
| **B1 / B2 / B3** | USB receiver base / cover / measuring blank (or substitute the final nominal/fitted bezel) |
| **C1 / C2** | Front-fastener base / cover |
| **D1 / D2 / D3** | Badge cover / plate with height gauges / gasket cutting-pattern aid |
| **E1** | 2u coupon: test against your MX switch and 2u plate-mount stabilizer |
| **F1** | 6.25u coupon: test against your MX switch and 6.25u plate-mount stabilizer |
| **G1** | Controller support jig: bears against the two actual socket plastic bodies |

E1, F1 and G1 test purchased hardware, not each other. D3 is a cutting aid:
use the soft foam gasket in the D1/D2 fit test, with the final light well and
badge. Do not include the label tab in the foam outline.

Labels are raised **0.6 mm**, with **0.8 mm strokes** and 4 mm-tall characters.
Tabs extend 12 mm beyond the part edge and avoid the mating geometry. Keep them
attached during testing. Their text faces away from the supplied print bed
orientation (including the upside-down plate/cover exports).

The **B3 USB blank** tab extends above the installed bezel. Its outer face and
the tab share the print bed; the raised label is on the upward-facing inner
side. Use the supplied orientation.

| Files | Purpose |
| --- | --- |
| `Cartridge-stack-coupon-{base,plate,dummy-PCB}` | Test both mounting stages, pass-through clearance, short inserts and screw lengths |
| `USB-bezel-fit-coupon-{base,cover}` | Test the removable USB insert's slots, stops and capture |
| `USB-bezel-blank` | Closed blank for measuring or drilling the final cable opening |
| `Front-fastener-fit-coupon-{base,cover}` | Test cover inserts, underside screw access and hard stops |
| `Logo-fit-coupon-cover` / `Logo-fit-coupon-plate-with-height-gauges` | Test the complete badge stack at the correct installed height |
| `Stabilizer-fit-coupon-{2u,6.25u}` | Check switch and stabilizer clip fit |
| `Controller-insertion-support-jig` | Temporary bench support for inserting the MCU into its sockets |
| `Logo-gasket-cutting-pattern-0.8mm` | Cutting-pattern reference; **do not install a rigid printed gasket** |

For the USB and badge trials, use the small installed parts from
[final-prints](../final-prints/README.md): the nominal USB bezel, light well and
badge. Those same parts can be used in the finished keyboard if their fit is good.
Socket shims and the foam cutting template are also in that folder.

See the [assembly guide](../README.md#coupons-and-prototype-checks) for hardware,
print settings and acceptance checks.
