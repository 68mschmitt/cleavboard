"""Hand-laid bottom-side USB pair and crystal circuit, ahead of matrix fan-in.
Coordinates are normal unmirrored board coordinates. In2 is their local GND reference.
"""
import pcbnew
def route_critical(b):
    from generate import track,via
    def path(net,points,width=.127):
        for a,c in zip(points,points[1:]):track(b,net,a,c,pcbnew.B_Cu,width)
    path('USB_DM',[(431.45,9.6),(432.0,9.6),(432.3,9.3),(432.7,9.3)])
    path('USB_DP',[(431.45,10),(432.0,10),(432.3,10.3),(432.7,10.3)])
    path('USB_N',[(433.7,9.3),(434.3,9.3),(434.7,9.7),(438.7,9.7),(439.4,10.4),(439.4,11.1),(440.05,11.75),(440.3625,11.75)])
    path('USB_P',[(433.7,10.3),(434.3,10.3),(434.5,10.1),(438,10.1),(438.7,10.8),(438.7,13),(439.35,13.65),(440.3625,13.65)])
    # Straight pass-through copper directly between each ESD channel's two lands.
    path('USB_N',[(440.3625,11.75),(442.6375,11.75)])
    path('USB_P',[(440.3625,13.65),(442.6375,13.65)])
    path('USB_N',[(442.6375,11.75),(443.455,11.75),(443.955,12.25),(444.955,12.25)])
    path('USB_P',[(442.6375,13.65),(443.45,13.65),(443.55,13.75),(444.955,13.75)])
    # Join both Type-C orientations with short bottom-only loops around the signal lands.
    path('USB_N',[(444.955,12.25),(445.8,12.25),(446.2,12.65),(446.2,12.85),(445.8,13.25),(444.955,13.25)])
    path('USB_P',[(444.955,12.75),(444.1,12.75),(443.85,13),(443.85,13.5),(444.1,13.75)])
    path('GND',[(440.3625,12.7),(439.4,12.7)],.3)
    v=via(b,'GND',439.4,12.7);v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
    path('XIN',[(424.55,11.6),(423.8,11.6),(422.85,12.55),(420.9,12.55)])
    path('XIN',[(420.9,12.55),(420.9,13.6),(420.5,14)])
    path('XOUT',[(424.55,11.2),(424,11.2),(424,9.55),(423.75,9.3),(422.5,9.3)])
    path('XTAL_OUT',[(421.5,9.3),(419.5,9.3),(418.7,10.1),(418.7,10.85),(417.1,10.85)])
    path('3V3',[(424.55,10.8),(425.1,10.8),(425.3,11)])
    path('3V3',[(423.5,10.8),(423.5,10.1),(423.6,10)])
    for x,y in [(425.3,11),(423.6,10)]:
        v=via(b,'3V3',x,y);v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2));v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
    for a,c in zip([(423.6,10),(423.6,10.4),(424.2,11)],[(423.6,10.4),(424.2,11),(425.3,11)]):track(b,'3V3',a,c,pcbnew.F_Cu,.127)
    # Regular QSPI escapes: six dedicated vias, two radial rows, no grid stairs.
    for net,y,vx in [('QSPI_SD3',11.6,430.8),('QSPI_SCLK',12,430.1),('QSPI_SD0',12.4,430.8),('QSPI_SD2',12.8,430.1),('QSPI_SD1',13.2,430.8),('QSPI_SS',13.6,432.25)]:
        path(net,[(431.45,y),(vx,y)])
        v=via(b,net,vx,y);v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2));v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
    for net,x,y,vy in [('QSPI_SS',433.095,16.35,15),('QSPI_SD1',434.365,16.35,15),('QSPI_SD2',435.635,16.35,15),('QSPI_SD0',436.905,23.65,25),('QSPI_SCLK',435.635,23.65,25),('QSPI_SD3',434.365,23.65,25)]:
        path(net,[(x,y),(x,vy)],.15)
        v=via(b,net,x,vy);v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
