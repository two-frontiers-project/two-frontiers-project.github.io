# General 3D Printing - Dremelfuge

> **Repository:** [2FP-3dPrinting](https://github.com/two-frontiers-project/2FP-3dPrinting)

---

# Dremelfuge

This folder contains files for printing and generating a Dremel-powered centrifuge, often called a "dremelfuge." The design uses common Eppendorf tubes and can be spun using a hand drill or rotary tool. The files include STL models ready for printing and the original OpenSCAD source so the design can be customized.

These parts were adapted from the open-source dremelfuge project (https://open-neuroscience.com/en/post/dremelfuge/). Please cite the original resource if using this repository. They allow quick, low-cost centrifugation without a dedicated bench-top centrifuge. Always follow appropriate safety precautions when operating a drill at high speed.

- **Dremelfuge_V4.scad**: OpenSCAD file for the primary rotor design.
- **Dremelfuge_V4.stl**: Pre-rendered STL of the rotor.
- **Dremelfuge_V4.gcode**: Example G-code for printers that require it.
- **Dremelfuge_Chuck_Edition_V4.stl**: Variation with an integral chuck to fit directly into a rotary tool.
- **shapes.scad**: Library of helper functions used by the OpenSCAD script.
