# Security, Privacy and Governance

## Version 1 deployment model

Local-first.

## Rules

- Do not upload source data to external services.
- Do not make external API calls for analysis.
- Do not store credentials.
- Do not persist source files unless the user explicitly exports or saves them.
- Do not unnecessarily display personal identifiers.
- Do not include source records in presentation exports unless required.
- Keep raw data separate from working analysis.

## Sensitive data

If the dataset contains names, emails, IDs or other personal data:

- minimise display
- avoid including identifiers in charts
- avoid exporting row-level personal data unless necessary
- document handling decisions

## Governance

Maintain:

- assumptions register
- limitations register
- audit trail
- metric definitions
- mapping record
- export record

## Decision-support disclaimer

The application supports analytical judgement.

It does not make operational decisions automatically.


