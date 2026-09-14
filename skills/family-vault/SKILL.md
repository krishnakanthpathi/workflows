---
name: family-vault
description: >-
  Manage family personal document vault storage, indexing, and retrieval in ~/Documents/FamilyVault. Handles interactive clarification, standardized filing (Dad, Mom, Me), registry logging, and document lookup.
version: 1.0.0
author: Krishna Kanth
license: MIT
metadata:
  tags: [family, documents, vault, obsidian, whatsapp, identity]
---

# Family Document Vault Skill

Manages the storage, organization, and retrieval of family personal documents (PAN, Aadhaar, Passport, Insurance, Licenses) with human-in-the-loop clarification.

---

## 1. Vault Location & Structure

* **Base Vault Path**: `~/Documents/Family Vault`
* **Default Members**: `Dad`, `Mom`, `Me` (or `Krishna`)
* **Layout**:
  ```text
  ~/Documents/Family Vault/
  ├── family.yaml                      # Family configuration and members schema
  ├── Registry.md (or notes/)          # Document ledger and note records
  └── files/                           # Stored files (organized by member)
      ├── dad/
      ├── mom/
      ├── krishna/
      └── Shared/
  ```

---

## 2. Ingestion & Storage Workflow

When a user sends or provides a document:

### Step A: Interactive Clarification
* **Never assume or silently auto-file.**
* If the user sends a file without full context, immediately ask:
  > *"What is this document about? (Whose document is it, and what type? e.g., Dad's PAN, Mom's Aadhaar)"*
* Wait for the user to confirm the family member and document type.

### Step B: Media Processing (Optional & Generic)
* If document metadata (like ID number or name) is not provided in text and needs to be extracted from an image/scan:
  * **Use any available media tool or skill** to inspect or OCR the document.
  * Do not rely on fixed paths—leverage whichever media processing tool is accessible in the current environment.
* If metadata is already provided by the user, **skip media processing** entirely and proceed directly to filing.

### Step C: Standardized Filing
* Move or copy the document to its member directory under `files/<member>/`.
* Enforce the naming convention:
  `<member>_<DocumentType>_<Identifier_or_Date>.<ext>`
* Examples:
  * `dad_PAN_ABCDE1234F.pdf`
  * `mom_Aadhaar_5678.pdf`
  * `krishna_Passport_Z1234567.pdf`

### Step D: Update the Ledger / Notes
* Record the document entry in the vault's ledger note (`notes/` or `Registry.md`) with the member, document type, ID, and file link.

---

## 3. Retrieval Workflow

When a user requests a document (e.g., *"Send Dad's PAN card"* or *"What is Mom's Aadhaar number?"*):

1. **Search Records**: Check the vault notes or ledger for the matching entry.
2. **Text Queries** (*"What is the number?"*):
   * Reply directly with the requested document number.
3. **File Queries** (*"Send the card / file"*):
   * Locate the file path under `files/<member>/<filename>`.
   * Deliver the file using the active platform's message/media delivery channel.
