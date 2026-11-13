# Populated KiCad previews

These are KiCad 10.0.8 raytraced views of revision 0.7 `../Cleaver.kicad_pcb`, including the
bundled component models. They are not separate artistic renders or mechanical
clearance approvals. See [model limitations](../Cleaver.3dshapes/README.md).

- [Rev0.7 top / switches and socketed controller](Cleaver-rev0.7-top.png)
- [Rev0.7 bottom / controller sockets, LEDs, diodes, capacitors](Cleaver-rev0.7-bottom.png)
- Historical rev0.6 direct-header views: [top](Cleaver-top.png), [bottom](Cleaver-bottom.png).

To recreate them from the repository root:

```sh
kicad-cli pcb render --output designs/module-rp2040/previews/Cleaver-rev0.7-top.png --width 2200 --height 900 --side top --zoom 2.3 --quality high designs/module-rp2040/Cleaver.kicad_pcb
kicad-cli pcb render --output designs/module-rp2040/previews/Cleaver-rev0.7-bottom.png --width 2200 --height 900 --side bottom --zoom 2.3 --quality high designs/module-rp2040/Cleaver.kicad_pcb
```

The interactive **Alt+3** viewer lets you rotate/zoom further. No keycaps, plate,
stabilizers, case, or USB cable are modeled. The RP2040-Plus module assembly and
header stack are explicitly approximate.
