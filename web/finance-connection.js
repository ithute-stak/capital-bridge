"use strict";
/*
 * Finance read integration contract.
 * The deployment's authenticated host MUST provide a function that makes an
 * authorized, same-origin API request. Tokens are never entered, logged or
 * stored by this demonstration page.
 */
(function () {
  const status = document.getElementById("live-status");
  const message = document.getElementById("live-message");
  const panel = document.getElementById("live-result");
  const button = document.getElementById("load-finance");
  const dateInput = document.getElementById("report-as-of");
  if (!button || !status || !message || !panel || !dateInput) return;
  dateInput.value = new Date().toLocaleDateString("en-CA");
  const money = minor => new Intl.NumberFormat("en-LS", {
    style: "currency", currency: "LSL"
  }).format(minor / 100);
  const companySelect = document.getElementById("finance-company");
  async function loadCompanies() {
    const provider = window.capitalBridgeFinanceSession;
    if (!companySelect || !provider || typeof provider.listCompanies !== "function") return;
    try {
      const companies = await provider.listCompanies();
      companySelect.replaceChildren(new Option("Select company", ""));
      companies.forEach(company => companySelect.add(new Option(company.name, company.id)));
      status.textContent = "Sign-in verified";
    } catch (_) {
      companySelect.replaceChildren(new Option("Sign in required", ""));
      status.textContent = "Not connected";
    }
  }
  if (companySelect) companySelect.addEventListener("change", async () => {
    const provider = window.capitalBridgeFinanceSession;
    panel.classList.add("hidden");
    if (!companySelect.value || !provider) return;
    try {
      await provider.selectCompany(companySelect.value);
      status.textContent = "Company selected";
    } catch (_) {
      status.textContent = "Access denied";
      companySelect.value = "";
    }
  });
  loadCompanies();
  button.addEventListener("click", async () => {
    // This callback is deliberately absent until a secure authenticated host
    // provides session management and an approved company selection.
    const provider = window.capitalBridgeFinanceSession;
    if (!provider || typeof provider.getFinanceOverview !== "function") {
      status.textContent = "Not connected";
      message.textContent = "A secure company sign-in and same-origin session integration are not configured. Demonstration data remains separate.";
      panel.classList.add("hidden");
      return;
    }
    button.disabled = true;
    status.textContent = "Loading";
    try {
      const data = await provider.getFinanceOverview({ asOf: dateInput.value });
      if (!data || data.currency !== "LSL" ||
          !["revenue_minor", "expense_minor", "operating_result_minor"].every(
             key => Number.isSafeInteger(data[key]))) {
        throw new Error("Unexpected finance response");
      }
      document.getElementById("live-revenue").textContent = money(data.revenue_minor);
      document.getElementById("live-expenses").textContent = money(data.expense_minor);
      document.getElementById("live-result-total").textContent = money(data.operating_result_minor);
      status.textContent = "Connected";
      message.textContent = "Authenticated posted-journal summary as of " + String(data.as_of || dateInput.value) + ". Separate from sample cards.";
      panel.classList.remove("hidden");
    } catch (error) {
      status.textContent = "Unavailable";
      message.textContent = "Financial data could not be loaded. Please verify your session, permissions and connectivity.";
      panel.classList.add("hidden");
    } finally {
      button.disabled = false;
    }
  });
})();
