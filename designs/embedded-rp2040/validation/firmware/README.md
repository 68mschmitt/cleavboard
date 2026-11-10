# Independent firmware build verification

Both `cleaver_embedded:default` and `cleaver_embedded:vial` compiled successfully
against Vial-QMK commit `dd43959ae5c08d8a28d38a1acf7b04e86b14a344`, using
`arm-none-eabi-gcc` 16.2.0. The exact versions, source hashes, output hashes, sizes,
and linked-symbol checks are recorded in [results.json](results.json).
Build logs are included here with terminal color sequences removed.

The copied build inputs were compared byte-for-byte with this project's firmware.
Both ELFs contain strong definitions of all five keyboard power/indicator hooks;
the Vial ELF also contains `vial_init` and `vialrgb_set_value`. Disassembly of
`backing_store_read_bulk` confirms the mapped EEPROM base `0x103fe000`, the final
8 KiB of the 4 MiB flash. This checks compiled behavior rather than just macros.

To reproduce, initialize the pinned checkout's submodules, copy `firmware/` to
`keyboards/cleaver_embedded/`, then run from the Vial-QMK checkout:

```sh
make cleaver_embedded:default -j4
make cleaver_embedded:vial -j4
arm-none-eabi-nm .build/cleaver_embedded_vial.elf
arm-none-eabi-objdump -d --disassemble=backing_store_read_bulk .build/cleaver_embedded_vial.elf
```

The generated UF2 files are not included as release binaries. These are build
and linkage results; USB enumeration, flash boot, suspend/resume, key scanning,
and LED current still require testing on assembled hardware.
