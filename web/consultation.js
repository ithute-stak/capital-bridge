"use strict";
(() => {
  const form = document.getElementById("consultation-form");
  const status = document.getElementById("consultation-status");
  if (!form || !status) return;
  form.addEventListener("submit", event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const values = new FormData(form);
    const name = String(values.get("name") || "").trim();
    const email = String(values.get("email") || "").trim();
    const phone = String(values.get("phone") || "").trim();
    const service = String(values.get("service") || "").trim();
    const message = String(values.get("message") || "").trim();
    if (!name || !email || !service || message.length < 10 || !values.has("consent")) {
      status.textContent = "Please complete the required details and consent checkbox.";
      return;
    }
    const subject = "CapitalBridge consultation enquiry: " + service;
    const body = [
      "Hello CapitalBridge Consultancy,",
      "",
      "I would like to request a consultation.",
      "",
      "Name: " + name,
      "Email: " + email,
      "Phone: " + (phone || "Not provided"),
      "Service: " + service,
      "",
      "Enquiry:",
      message,
      "",
      "Please contact me to discuss the next steps."
    ].join("\n");
    status.textContent = "Your email application will open with a prepared enquiry. Please review and send it; this website has not submitted it.";
    window.location.href = "mailto:tjlepekola@gmail.com?subject=" +
      encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
  });
})();