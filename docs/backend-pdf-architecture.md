# Server-only PDF rendering architecture

**Hard boundary:** all official CapitalBridge ONE PDF bytes are composed by trusted backend services. Browser code must never render, sign, apply an official company logo or calculate authoritative document totals. No `jsPDF`, `pdfmake`, `html2pdf`, browser print-to-PDF or front-end canvas exports for official records.

Backend Python provides `api/quotation_pdf.py` with an initial ReportLab A4 quotation renderer. All other services (Java approvals, C++ deterministic arithmetic, Go event delivery, Rust hashing, Python APIs) may feed verified records to the backend PDF workflow, but none of the browsers produce files.

Rendering prerequisites:
1. Resolve a verified Ithute session and company authorisation server-side.
2. Fetch a versioned, approved business logo from a server-controlled asset path — never a user-provided arbitrary path. If missing, **refuse official publication**.
3. Load a complete approved quotation and line items from one company-scoped database transaction.
4. Recompute totals from immutable integer minor-unit data; verify the stored subtotal/tax against the approved transaction before calling the renderer. Tax policies must be checked separately.
5. Render on backend, archive with template version, company/document identity, actor, SHA-256 and audit trail.
6. Expose only an authorisation-checked backend PDF download endpoint with `application/pdf`, `Content-Disposition: attachment`, `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`.
7. Carry out rendered-page inspection, page-overflow checks and end-to-end database security tests.

**Implementation status:** the renderer is currently a backend library only. No download route is mounted, no production-approved logo has been provisioned, and there is no claim of a deployed/document archival system.
