# Server-side OIDC code exchange

`api/oidc_exchange.py` exchanges an authorization code with a configured, trusted HTTPS token endpoint using PKCE and delegates signed ID-token validation to `api/oidc_verify.py`. It never accepts identity claims from the browser.

The implementation **does not expose a live login route**, create cookies, or enable production authentication. Before wiring it in, securely persist OIDC transactions server-side, **atomically consume each transaction once**, bind it to the initiating browser, verify provider discovery metadata and allowed redirect paths, apply request limits, authenticate the subject against a trusted user registry, and issue durable sessions only after verified identity mapping. Enforce network egress restrictions against SSRF, TLS validation, and deployment-specific OIDC client authentication requirements.

Token exchange and ID-token checks are necessary but not sufficient for end-to-end login security.
