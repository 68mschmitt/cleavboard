// Cleaver rev0.9: replaceable badge, millimetres, face down.
// Render "blank" for a translucent insert. For two-colour printing, export
// "mask" and "diffuser" separately and load them together at the SAME origin.
// Edit mark() or import a centred SVG inside the 47.8 x 22.4 mm design area.
// The 53.8 x 28.4 mm flange and 50.8 x 25.4 mm body are the mechanical interface.
part = "blank"; // [blank,mask,diffuser]
face = [50.8, 25.4];
flange = [53.8, 28.4];
bore = [48.8, 23.4];
flange_z = 2.60000;
flange_thickness = 0.8;
diffuser_thickness = 1.0;
mask_thickness = 0.4;

module sq(size) { square(size,center=true); }
module mark() { text("C",size=18,halign="center",valign="center",font="Liberation Sans:style=Bold"); }
module blank() {
    difference() {
        union() {
            linear_extrude(flange_z) sq(face);
            translate([0,0,flange_z]) linear_extrude(flange_thickness) sq(flange);
        }
        translate([0,0,diffuser_thickness])
            linear_extrude(flange_z+flange_thickness) sq(bore);
    }
}
module mask() {
    linear_extrude(mask_thickness)
        difference() { sq(face); intersection() { sq(bore-[1,1]); mirror([0,1,0]) mark(); } }
}
// The Y mirror keeps lettering readable after turning the face-down print over.
translate([flange[0]/2,flange[1]/2,0]) {
    if (part == "blank") blank();
    else if (part == "mask") mask();
    else if (part == "diffuser") difference() { blank(); mask(); }
}
