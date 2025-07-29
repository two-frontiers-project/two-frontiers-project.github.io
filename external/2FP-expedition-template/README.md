# Expedition Template

> **Repository:** [2FP-expedition-template](https://github.com/two-frontiers-project/2FP-expedition-template)

---

# Expedition Template

This repository provides a basic folder structure and a set of spreadsheets for planning and documenting a field expedition. Each spreadsheet uses `###EXPEDITIONNAME###` as a placeholder so they can be renamed to match the name of a specific expedition.

## Contents

- `initialize_expedition.py` – small script used to replace the `###EXPEDITIONNAME###` placeholder in filenames with your actual expedition name.
- `###EXPEDITIONNAME###_BUDGET_AND_EXPENSES.xlsx` – track the overall budget.
- `###EXPEDITIONNAME###_CONCEPT_OF_OPERATIONS.docx` – Word document describing how the expedition will be run.
- `###EXPEDITIONNAME###_DEBRIEF.xlsx` – template for recording post-expedition notes.
- `###EXPEDITIONNAME###_INVENTORY_AND_TRANSPORT.xlsx` – spreadsheet for tracking gear and transport logistics.
- `###EXPEDITIONNAME###_SAMPLING_AND_METADATA.xlsx` – template for recording samples and associated metadata.
- `###EXPEDITIONNAME###_TEAM_AND_TRAVEL.xlsx` – roster and travel information for the expedition team.

### Folders

- `ADDITIONAL_DATA` – place any extra data collected in the field.
- `BACKGROUND_RESEARCH` – reference papers or other materials.
- `FORMS` – blank forms such as liability and photo releases.
- `MAPS` – maps of your sampling sites.
- `PERMITTING` – copies of permits and related documentation.
- `PHOTOS` – photos collected during sampling (consider scientific vs. non‑scientific subfolders).
- `PROTOCOLS` – all protocols to be used in the field.
- `RECEIPTS_TICKETS_CONFIRMATIONS`
  - `RECEIPTS` – keep receipts, ideally one folder per participant.
  - `TICKETS` – store copies of travel tickets.
  - `CONFIRMATIONS` – hotel/lodging confirmations and similar information.

## Usage

1. Clone the template:

   ```bash
   git clone <repository-url>
   cd 2FP-expedition-template
   ```

2. Rename the placeholder files by running the initialization script. The script simply renames files and prints what changed:

   ```bash
   python initialize_expedition.py --name YOUR_EXPEDITION_NAME
   ```

   The script searches for `###EXPEDITIONNAME###` in filenames and replaces it with the name you provide.

3. (Optional) Upload the entire folder to a shared Google Drive so every collaborator can access the documents.

4. The spreadsheets are in Microsoft Office formats. If you don’t have Office, you can open them with OpenOffice. You can also convert them to CSV files, but multi‑tab spreadsheets will lose functionality when converted.

## Contact

info at two frontiers dot org

