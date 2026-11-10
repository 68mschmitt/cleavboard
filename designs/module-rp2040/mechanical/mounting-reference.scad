// Import into your case design. PCB top is Z=0, bottom Z=-1.6.
// XY origin is upper-left; Y is negative toward the keyboard front.
pcb_size = [452.4375, 147.6375, 1.6];
mounts = [[4, -4], [110, -23.8], [220, -23.8], [330, -23.8], [395, -26], [313, -70], [4, -143], [90, -138], [220, -138], [365, -138], [448, -138]];
module mounting_axes(height=20) { for(p=mounts) translate([p[0],p[1],-10]) cylinder(d=2.2,h=height,$fn=48); }
module standoff_envelopes(height=3.5) { for(p=mounts) translate([p[0],p[1],0]) cylinder(d=6,h=height,$fn=48); }
mounting_axes();
