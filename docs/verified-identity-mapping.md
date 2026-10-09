# Registered external identities

A trusted administrator must provision an exact OIDC `issuer` + `subject` tuple against an existing internal user identifier. The authentication callback may resolve this mapping **only after** the ID token's signature, issuer, audience, time claims and nonce have been verified. Unregistered identities fail closed. No email-based matching, automatic account creation, or privilege grants happen during authentication.

`cb.external_identities` is deliberately inaccessible to PUBLIC. Production provisioning must use an audited administrator-controlled path with uniqueness and referential-integrity safeguards linked to a real users table. A separate restricted login service database role will need narrowly scoped permission. The mapping is not wired to a working login endpoint, and no sessions are issued by this change.
