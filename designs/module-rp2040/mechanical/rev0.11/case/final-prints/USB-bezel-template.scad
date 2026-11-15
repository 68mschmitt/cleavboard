// Millimetres. Printed outer face down; assembled PCB +Y is toward the user.
// Positive dy moves the opening toward the keyboard front; positive dz raises it.
// Set blank=true to print a closed measuring/drilling blank.
dy=0.0; dz=0.0; opening_w=16.0; opening_h=7.2; blank=false;
outer_w=24.0; flange_w=28.0;
outer_bottom=-2.0; outer_top=10.8;
center_y=14.5; nominal_y=13.39; nominal_z=5.74;
assert(nominal_y+dy-opening_w/2 >= center_y-outer_w/2+1);
assert(nominal_y+dy+opening_w/2 <= center_y+outer_w/2-1);
assert(nominal_z+dz-opening_h/2 >= outer_bottom+1);
assert(nominal_z+dz+opening_h/2 <= outer_top-1);
difference() {
  union() {
    translate([(flange_w-outer_w)/2,0,0]) cube([outer_w,outer_top-outer_bottom,2.0]);
    translate([0,1.0,2.0])
      cube([flange_w,9.4,1.8]);
  }
  if(!blank) translate([flange_w/2+nominal_y-center_y+dy-opening_w/2,nominal_z+dz-outer_bottom-opening_h/2,-1])
    cube([opening_w,opening_h,10]);
}
