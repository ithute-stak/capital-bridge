"use strict";
// Read server-side rollout state; browser state can never activate sign-in.
(async () => {
  const button = document.getElementById("sign-in");
  const notice = document.getElementById("login-notice");
  if (!button || !notice) return;
  button.disabled = true;
  try {
    const response = await fetch("/api/v1/auth/readiness", {
      credentials: "same-origin", cache: "no-store",
      headers: {"Accept": "application/json"}, redirect: "error",
    });
    if (!response.ok) throw Error("Readiness unavailable");
    const state = await response.json();
    // A readiness value alone is NOT an authenticated login route.
    // Never use a browser value to bypass backend activation controls.
    notice.textContent = state.sign_in_available === false
      ? "Secure sign-in is not yet available. The authentication service is undergoing configuration and security review."
      : "Login activation requires verified backend session integration. Contact your administrator.";
  } catch (_) {
    notice.textContent = "Authentication status is unavailable. Secure sign-in remains disabled.";
  }
})();
