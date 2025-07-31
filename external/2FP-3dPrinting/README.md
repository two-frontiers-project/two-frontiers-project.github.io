# General 3D Printing

> **Repository:** [2FP-3dPrinting](https://github.com/two-frontiers-project/2FP-3dPrinting)

---

# 2FP-3dPrinting

This repository collects a variety of 3D printable designs that we have used in our lab for experiments, instrument modifications, and general convenience. Each subdirectory contains the design files for a specific project, typically including OpenSCAD source code and ready-to-print STL models. Many of these parts were created to solve small problems around the lab or to interface equipment in novel ways.

Below is an overview of every design included here. Each folder also has its own README with more concise instructions.

## Dremelfuge
The dremelfuge is a rotor that fits common microcentrifuge tubes and spins in a rotary tool such as a Dremel or drill. It is handy when a benchtop centrifuge is not available or when small samples must be spun quickly. Files in the `dremelfuge` folder include the OpenSCAD source, STL models, an optional chuck edition, and example G-code. Always take care when using a drill as a centrifuge and wear eye protection.

## Eyeglasses Dive Mask Mount
Ever wanted to wear your prescription glasses underwater? The `eyeglasses_divemask_mount` folder contains a custom mount that snaps into a standard dive mask and holds eyeglass lenses in place. The design is parametric so you can tweak lens spacing or orientation. Several SVG files provide 2D outlines for reference or laser cutting, and there are two generations of SCAD/STL models.

## Fluorometer Collimating Lens Mount
This mount is used to position a collimating lens for fiber-optic fluorescence measurements. It keeps the lens aligned with the optical path of a fluorometer. Both the main mount and a removable spacer are provided. If your lens diameter or focal length differs, open the SCAD files to adjust the parameters accordingly.

## Laser Cutter Racks
We sometimes cut quick organizers out of cardboard or acrylic. The `laser_cutter_racks` directory includes two simple SVG patterns: one for a rack that holds anaerobic jars and another for transporting larger sample jars. Import these into your laser cutter software, set the material thickness, and cut away.

## Microscope Mount for Fiber Spectrophotometer
To capture spectra directly from microscope slides, we designed an adapter that clamps an Ocean Optics fiber probe onto a microscope. This lets us collect light from a sample while viewing it. The OpenSCAD file can be tuned to match different microscopes or probes, and the provided STL is ready to print.

## pH Bottle Holder
pH electrodes are usually stored in a small bottle of buffer solution. This holder keeps that bottle upright and secure on the bench. Two variants are available: a regular version and a more solid hull version. Choose whichever suits your printing preference and adjust the SCAD variables for different bottle sizes.

## Spectrophotometer Adapters
Working with spectrophotometers often requires custom stands or adapters. The `spec_adapters` folder contains parametric designs for cuvette adapters and stands. You will find both elaborate and simplified stands along with preview images and G-code. Mix and match the pieces to position samples or optical fibers precisely.

## Turbidometer Adapters
Finally, the `turbidometer_adapters` directory houses adapters that allow standard test tubes to be used in a turbidometer. Several iterations are included so you can choose the model that matches your instrument and tube size. One of the files also stores a snapshot of recommended print settings.

We hope these pieces make your experiments a little easier or inspire new projects. Happy printing!
