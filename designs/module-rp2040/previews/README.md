# Populated KiCad previews

These are KiCad 10.0.8 raytraced views of revision 0.5 `../Cleaver.kicad_pcb`, including the
bundled component models. They are not separate artistic renders or mechanical
clearance approvals. See [model limitations](../Cleaver.3dshapes/README.md).

- [Top / switches and controller](Cleaver-top.png)
- [Bottom / sockets, LEDs, diodes, capacitors](Cleaver-bottom.png)

To recreate them from the repository root:

```sh
kicad-cli pcb render --output designs/module-rp2040/previews/Cleaver-top.png --width 2200 --height 900 --side top --zoom 2.3 --quality high designs/module-rp2040/Cleaver.kicad_pcb
kicad-cli pcb render --output designs/module-rp2040/previews/Cleaver-bottom.png --width 2200 --height 900 --side bottom --zoom 2.3 --quality high designs/module-rp2040/Cleaver.kicad_pcb
```

The interactive **Alt+3** viewer lets you rotate/zoom further. No keycaps, plate,
stabilizers, case, USB cable, or TP1 wire are modeled. The YD module assembly and
header stack are explicitly approximate.
