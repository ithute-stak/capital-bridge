"use strict";
(() => {
  const form = document.getElementById("consultation-form");
  const status = document.getElementById("consultation-status");
  if (!form || !status) return;
  let submitting = false;
  function mailto(data) {
    const subject = "CapitalBridge consultation enquiry: " + data.service;
    const body = [
      "Hello CapitalBridge Consultancy,", "",
      "I would like to request a consultation.", "",
      "Name: " + data.name, "Email: " + data.email,
      "Phone: " + (data.phone || "Not provided"),
      "Service: " + data.service, "", "Enquiry:",
      data.message, "", "Please contact me to discuss the next steps."
    ].join("\n");
    status.textContent = "Your email application will open with a prepared enquiry. Please review and send it; this website has not submitted it.";
    window.location.href = "mailto:tjlepekola@gmail.com?subject=" +
      encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
  }
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (submitting || !form.reportValidity()) return;
    const values = new FormData(form);
    const data = {
      name: String(values.get("name") || "").trim(),
      email: String(values.get("email") || "").trim(),
      phone: String(values.get("phone") || "").trim(),
      service: String(values.get("service") || "").trim(),
      message: String(values.get("message") || "").trim(),
      consent: values.has("consent")
    };
    if (!data.name || !data.email || !data.service || data.message.length < 10 || !data.consent) {
      status.textContent = "Please complete the required details and consent checkbox.";
      return;
    }
    submitting = true;
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;
    try {
      const readiness = await fetch("/api/v1/consultations/intake/readiness", {
        credentials: "same-origin", cache: "no-store"
      });
      if (!readiness.ok) { mailto(data); return; }
      const state = await readiness.json();
      if (state.online_submission_available !== true) { mailto(data); return; }
      status.textContent = "Submitting your consultation request…";
      const response = await fetch("/api/v1/consultations", {
        method: "POST", headers: {"Content-Type":"application/json"},
        credentials: "same-origin", cache: "no-store", body: JSON.stringify(data)
      });
      if (!response.ok) {
        status.textContent = response.status === 429
          ? "Too many requests. Please wait before trying again."
          : "Your enquiry was not confirmed. Please try again later or contact us by email.";
        return;
      }
      const result = await response.json();
      if (result.received !== true) throw Error("Unconfirmed submission");
      form.reset();
      status.textContent = "Your consultation enquiry was received. Thank you.";
    } catch (_) {
      status.textContent = "Unable to confirm submission. Please contact us by email; do not resubmit until you check whether it arrived.";
    } finally {
      submitting = false;
      if (button) button.disabled = false;
    }
  });
})();
