# CapitalBridge ONE — official document production standard

Applies to quotations, invoices, receipts, client letters, engagement reports, statements, certificates and case correspondence.

## Brand assets
- The **official approved CapitalBridge logo** is mandatory on final client-facing PDFs. Store a production-approved original in the brand asset registry with a version, maintainer and explicit approval record. Do not invent, redraw or substitute a text badge/logo.
- Where no approved logo asset is available, block final publication and label previews **DRAFT — BRAND ASSET NOT VERIFIED**. Never ship an unlabeled logo-free document as official.
- Use company legal name **CapitalBridge Consultancy (Pty) Ltd**; verify registered address, contact details and tax identifiers before printing. Never fabricate banking or regulatory details.

## Professional page design
- White A4 portrait pages, 18–22 mm margins, uncluttered grid and consistent alignment.
- Restrained navy / charcoal / subtle teal palette, accessible contrast, polished typography with clear type hierarchy.
- Header: approved logo, legal business name and verified business contact; footer: document reference, issue date, page number and business identity.
- Financial tables: right-aligned monetary values, Maloti/LSL display, consistent two decimal places, grouped line items, prominent total and tax breakdown.
- Long tables repeat column headings across pages; do not split financial line items across page boundaries when avoidable.
- Quotations: client identity, unique reference, issue and expiry dates, line item descriptions, quantities, unit prices, subtotal, tax basis, amount due, terms and authorised approval status.
- Do not embed unapproved handwritten signatures; require explicit authorisation to use signed assets.

## Data integrity and publication gates
- Render from authorised, company-scoped server data, never the demo dashboard arrays or browser-submitted totals.
- Recompute quotation totals from persisted line items using integer minor units; verify discounts and taxes using approved policy before publication.
- Require an accepted workflow state before labelling a quotation an official issued document.
- Produce PDF/A if appropriate for long-term preservation and embed legible fonts; verify every page visually before release.
- Generate a record of template version, company, document UUID, approver, renderer version and SHA-256 checksum. Access and downloads require company membership.
- Never include placeholder data, sample banking details, or unverified tax assumptions in final documents.

## Deployment note
These rules are design and release acceptance criteria, **not a claim that a PDF generation service is already deployed**. An approved logo and production rendering integration must be completed before official PDF publication.
