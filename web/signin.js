"use strict";
// The browser cannot enable OIDC. The server must explicitly advertise a
// same-origin launch path after deployment-specific OIDC checks pass.
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
    // Only one hardcoded same-origin route can launch the login handshake.
    // No arbitrary URL from an API response is ever followed.
    if (state.sign_in_available === true && state.provider === "ithute"
        && state.start_path === "/api/v1/oidc/start") {
      button.disabled = false;
      notice.textContent = "Secure sign-in uses Ithute Auth. Continue to authenticate.";
      button.addEventListener("click", () => {
        window.location.assign("/api/v1/oidc/start");
      }, {once: true});
    } else {
      notice.textContent = "Secure Ithute sign-in is not yet available. No credentials are collected here.";
    }
  } catch (_) {
    notice.textContent = "Authentication status is unavailable. Secure sign-in remains disabled.";
  }
})();
