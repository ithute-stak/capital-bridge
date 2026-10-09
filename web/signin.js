"use strict";
// Login is unavailable until trusted backend BFF setup and security review.
// Never collect passwords, bearer tokens or identities in demonstration HTML.
(() => {
  const button = document.getElementById("sign-in");
  const notice = document.getElementById("login-notice");
  if (!button || !notice) return;
  const configured = window.capitalBridgeLoginReady === true;
  // No browser-global toggle can activate login: fail closed unconditionally.
  button.disabled = true;
  notice.textContent = configured
    ? "The identity service requires server-side activation and verification before sign-in can begin."
    : "Secure sign-in is being configured. No user credentials are collected on this page.";
})();
