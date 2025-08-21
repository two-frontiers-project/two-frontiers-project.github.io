# Sample Identifiers and Site Metadata

## Background
Sample identifiers are the backbone of traceability in 2FP’s workflows, ensuring every collected specimen can be tracked from the moment of field collection to long-term storage and final data analysis. Consistent, unambiguous identifiers are essential for reproducibility, data integration, and sharing with collaborators. Complete metadata must be collected at the time of sampling, never reconstructed later, to maintain accuracy and enable replication.

## Protocols

### Field IDs versus CUAL-IDs (CIDs)
We use two forms of identifiers for every sample:

##### Field ID
A short, human-readable code written directly on the collection container (e.g., Whirl-Pak, 50 mL conical). This serves as the primary reference during fieldwork. Field IDs can be simple numbers (1, 2, 3…) or can include metadata about sample type (e.g., S1, S2 for sediment; W1, W2 for water). Field IDs are assigned and labeled on containers before heading into the field, and all handwritten metadata recorded during collection should reference the Field ID. Because Field IDs are tied to a specific expedition and context, they can be reused between different sampling campaigns — but never within the same expedition.

##### CUAL-ID (CID)
A unique, permanent alphanumeric hash assigned during Sample Check-In back at the lab. Each CID is pre-generated, printed on cryolabel sheets prior to field deployment, and mapped to the sample’s Field ID immediately upon check-in. The CID label is applied to the original collection container and later to all aliquots or preserved fractions (e.g., glycerol, DMSO, DNA Shield tubes). Once assigned, a CID is never reused under any circumstances.

### Minimum metadata to collect in the field
- At the time of sampling, record the following for each sample:
- GPS coordinates in decimal degrees (DD), WGS 84 datum
- Date and time of collection (local time)
- Field ID and assigned CID
- Collector initials
- Sampling method and preservation method used
- Environmental notes (e.g., turbidity, temperature, flow, substrate type)
- Site photographs and GPS screenshots

### Metadata recording and handling
Metadata should be recorded both digitally and in a backup field notebook. At least one device per team must be capable of GPS logging, and all devices should be time-synced before fieldwork begins. Avoid apps or tools that auto-convert coordinate formats or datums without clear indication or transparency.
When using environmental sensors such as pH, dissolved oxygen, or salinity probes, log calibration settings and measurement conditions alongside each reading. Capture redundant measurements and photographs whenever possible to safeguard against data loss.

### Best practices
- Prepare and label all Field ID containers before field deployment.
- Carry spare pre-labeled containers for unplanned samples, but document any new IDs in the metadata sheet before collection.
- Use permanent, alcohol-resistant markers or thermal labels to prevent fading in wet or abrasive conditions.
- Apply CID labels only in a clean, organized Check-In area to avoid mislabeling.
- Immediately update the expedition metadata file with the Field ID → CID mapping and upload to the cloud folder.
- Cross-check GPS coordinates and photos before leaving a site to ensure data completeness.
- For multi-day expeditions, upload digital metadata daily to the designated expedition cloud folder and verify backups are intact.

