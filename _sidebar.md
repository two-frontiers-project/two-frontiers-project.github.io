<img src="images/2FP-Logo-MainLogo-COLOR-2063x500.png" alt="Two Frontiers Project" width="1032" />

<script>
function toggleHandbookSection(linkElement) {
  // Only handle Field Handbook links
  if (!linkElement.href.includes("2FP-Field-Handbook")) return;
  
  const listItem = linkElement.parentElement;
  const existingSubsections = listItem.querySelector(".handbook-subsections");
  
  if (existingSubsections) {
    // Toggle existing subsections
    existingSubsections.style.display = existingSubsections.style.display === "none" ? "block" : "none";
    return;
  }
  
  // Create subsections container
  const subsectionsDiv = document.createElement("div");
  subsectionsDiv.className = "handbook-subsections";
  subsectionsDiv.style.paddingLeft = "20px";
  subsectionsDiv.style.marginTop = "5px";
  
  // Add loading indicator
  subsectionsDiv.innerHTML = "Loading subsections...";
  listItem.appendChild(subsectionsDiv);
  
  // Fetch the markdown file to extract headers
  fetch(linkElement.href)
    .then(response => response.text())
    .then(content => {
      const headers = extractHeadersFromMarkdown(content);
      if (headers.length > 0) {
        const subsectionsList = document.createElement("ul");
        headers.forEach(header => {
          const li = document.createElement("li");
          const anchor = header.text.toLowerCase().replace(/[^a-z0-9]+/g, "-");
          const link = document.createElement("a");
          link.href = linkElement.href + "#" + anchor;
          link.textContent = header.text;
          li.appendChild(link);
          subsectionsList.appendChild(li);
        });
        subsectionsDiv.innerHTML = "";
        subsectionsDiv.appendChild(subsectionsList);
      } else {
        subsectionsDiv.innerHTML = "No subsections found";
      }
    })
    .catch(error => {
      subsectionsDiv.innerHTML = "Error loading subsections";
      console.error("Error:", error);
    });
}

function extractHeadersFromMarkdown(content) {
  const lines = content.split("\n");
  const headers = [];
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("#")) {
      const level = trimmed.length - trimmed.replace(/^#+/, "").length;
      const text = trimmed.replace(/^#+\s*/, "").trim();
      if (text.length > 3) {
        headers.push({ level, text });
      }
    }
  }
  
  return headers;
}
</script>
<style>
.handbook-subsections ul {
  list-style-type: none;
  padding-left: 0;
}
.handbook-subsections li {
  margin: 2px 0;
}
.handbook-subsections a {
  color: #ccc;
  text-decoration: none;
  font-size: 0.9em;
}
.handbook-subsections a:hover {
  color: #fff;
  text-decoration: underline;
}
</style>

## Overview
- [Home](/README.md)

## The Two Frontiers Handbook
- [The Two Frontiers Handbook](external/2FP-Field-Handbook/README.md)
  - [About This Handbook - About This Handbook](external/2FP-Field-Handbook/01-about-this-handbook.md)
  - [Expedition Planning - Expedition Planning](external/2FP-Field-Handbook/02-expedition-planning.md)
  - [Sample Identifiers - Sample Identifiers And Site Metadata](external/2FP-Field-Handbook/03-sample-identifiers-and-site-metadata.md)
  - [Preparation - Preparation For Sample Collection](external/2FP-Field-Handbook/04-preparation-for-sample-collection.md)
  - [Field Lab Setup - Setting Up A Field Processing Lab](external/2FP-Field-Handbook/05-setting-up-a-field-processing-lab.md)
  - [Sample Collection - Sample Collection](external/2FP-Field-Handbook/06-sample-collection.md)
  - [Sample Check-In - Sample Check In](external/2FP-Field-Handbook/07-sample-check-in.md)
  - [Sample Processing - Sample Processing And Preservation](external/2FP-Field-Handbook/08-sample-processing-and-preservation.md)
  - [Sample Transportation - Sample Transportation](external/2FP-Field-Handbook/09-sample-transportation.md)
  - [Post-Sampling - Post Sampling Reset And Team Debrief](external/2FP-Field-Handbook/10-post-sampling-reset-and-team-debrief.md)

## Speciality Kits
- [Speciality Kits](external/2FP-fieldKitsAndProtocols/README.md)
  - [Citizen Science Extremophiles In The Home](external/2FP-fieldKitsAndProtocols/citizen_science_extremophiles_in_the_home/README.md)
  - [Kit 10Sample Collection Nobanking](external/2FP-fieldKitsAndProtocols/kit_10sample_collection-nobanking/README.md)

## Hardware
- [General 3D Printing](external/2FP-3dPrinting/README.md)
  - [Dremelfuge](external/2FP-3dPrinting/dremelfuge/README.md)
  - [Turbidometer Adapters](external/2FP-3dPrinting/turbidometer_adapters/README.md)
  - [Spec Adapters](external/2FP-3dPrinting/spec_adapters/README.md)
  - [Eyeglasses Divemask Mount](external/2FP-3dPrinting/eyeglasses_divemask_mount/README.md)
  - [Ph Bottle Holder](external/2FP-3dPrinting/pH_bottle_holder/README.md)
  - [Microscope Mount For Fiber Spectrophotometer](external/2FP-3dPrinting/microscope_mount_for_fiber_spectrophotometer/README.md)
  - [Laser Cutter Racks](external/2FP-3dPrinting/laser_cutter_racks/README.md)
  - [Fluorometer Collimating Lens Mount](external/2FP-3dPrinting/fluorometer_collimating_lens_mount/README.md)
- [PUMA Scope](external/2FP-PUMA/README.md)
  - [Freecad](external/2FP-PUMA/FreeCAD/README.md)
- [Cuvette Holder](external/2FP-cuvette_holder/README.md)
- [General Field Tools](external/2FP-fieldworkToolsGeneral/README.md)
  - [Uvspec](external/2FP-fieldworkToolsGeneral/UVspec/README.md)
  - [Od600](external/2FP-fieldworkToolsGeneral/OD600/README.md)
- [Open Colorimeter](external/2FP-open_colorimeter/README.md)

## Software
- [XTree](external/2FP-XTree/README.md)
- [MAGUS](external/2FP_MAGUS/README.md)

## Templates
- [Expedition Template](external/2FP-expedition-template/README.md)
  - [Maps](external/2FP-expedition-template/MAPS/README.md)
  - [Background Research](external/2FP-expedition-template/BACKGROUND_RESEARCH/README.md)
  - [Forms](external/2FP-expedition-template/FORMS/README.md)
  - [Additional Data](external/2FP-expedition-template/ADDITIONAL_DATA/README.md)
  - [Receipts Tickets Confirmations](external/2FP-expedition-template/RECEIPTS_TICKETS_CONFIRMATIONS/README.md)
  - [Photos](external/2FP-expedition-template/PHOTOS/README.md)
  - [Protocols](external/2FP-expedition-template/PROTOCOLS/README.md)
  - [Permitting](external/2FP-expedition-template/PERMITTING/README.md)

