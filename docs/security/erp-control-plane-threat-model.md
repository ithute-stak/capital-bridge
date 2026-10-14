# ERP platform control plane — identity threat model

**Implementation status:** tenant registration, lifecycle and operator registry SQL
exist on the feature branch. There is no externally accessible control-plane API
and no deployment-approved platform operator login. Do not grant the
`cb_erp_control_plane` role to the general finance API database user.

## Critical authentication boundary

`cb.authorized_user()` is based on transaction-local
`app.user_id` configuration. PostgreSQL custom settings are *not* independent
proof of identity: a client with a SQL connection that can set both the supplied
operator UUID and `app.user_id` could impersonate an enrolled operator.

**Do not treat the SQL operator registry check alone as sufficient for a public
or general application control plane.** A trusted gateway must verify the
Ithute Auth token (issuer, audience, signature, expiry), derive the subject on
the server and execute control-plane SQL with a separately restricted credential.
No arbitrary SQL access or caller-supplied identity can reach that credential.
Deployment must be blocked until this binding is independently security tested.

## Tests in this milestone

`db/tests/erp_operator_security.sql` verifies that mismatched caller
identity, revoked operator identity and registry self-enrollment are rejected
under the restricted control-plane role. These are necessary but **not
sufficient** tests: a malicious SQL client setting both identity values remains
a threat to be eliminated by authenticated network and database boundaries.

Future acceptance requires cross-tenant denial, role-revocation tests,
authenticated API negative tests, rate limiting, immutable audit export,
two-person approval of operator enrollment and secrets rotation.
