// Color study only; uses the verified 19-bottom-hole case without geometry edits.
use <../../hop-ban-chai-dien.scad>
preview_color = "#E8C4D2"; // approximate pastel pink from the supplied photo
color(preview_color) {
    translate([-62,0,0]) assembled();
    body();
    translate([58,0,0]) cap();
}
